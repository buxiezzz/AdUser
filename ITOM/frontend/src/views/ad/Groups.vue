<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">安全策略组台账</h1>
      <el-button type="primary" :icon="Refresh" @click="fetchGroups" :loading="loading" plain>
        重新拉取同步
      </el-button>
    </div>

    <!-- 顶部状态提示 -->
    <el-alert
      title="这里展示了 AD 中实际运作的所有安全组。点击对应安全组右侧的「成员管控」即可实时查看并调整被赋予该组权限的人员。"
      type="info"
      show-icon
      :closable="false"
      class="border border-indigo-100 bg-indigo-50 text-dark"
    />

    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <div class="mb-5 flex items-center justify-between">
        <el-input 
          v-model="searchQuery" 
          placeholder="在列表中查找安全组名称..." 
          :prefix-icon="Search"
          class="w-80"
          clearable
        />
        <div class="text-sm text-gray-500">共加载到 {{ filteredGroups.length }} 个安全组</div>
      </div>

      <el-table :data="filteredGroups" style="width: 100%" v-loading="loading" border stripe>
         <el-table-column type="index" label="序号" width="80" align="center" />
         <el-table-column label="组名 (CN)" width="300">
           <template #default="{ row }">
             <span class="font-medium text-gray-800">
               {{ extractCN(row) }}
             </span>
           </template>
         </el-table-column>
         <el-table-column label="完整区别名路径 (DN)">
           <template #default="{ row }">
             <span class="text-sm text-gray-500 font-mono">{{ row }}</span>
           </template>
         </el-table-column>
         <el-table-column label="操作" width="120" fixed="right">
           <template #default="{ row }">
             <el-button link type="primary" size="small" @click="openGroupDetail(row)">
               组成员管控
             </el-button>
           </template>
         </el-table-column>
      </el-table>
      
      <div class="mt-4 flex justify-end">
        <span class="text-sm text-gray-500">共加载到 {{ filteredGroups.length }} 个安全组</span>
      </div>
    </el-card>

    <!-- 成员管控侧边栏抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`正在配属: ${extractCN(currentGroupDn)}`"
      size="850px"
      append-to-body
      destroy-on-close
    >
      <div v-loading="detailLoading" class="px-2 h-full flex flex-col">
        <div class="mb-4 text-sm text-gray-500 bg-gray-50 p-3 rounded">
          <strong>真实路径:</strong> <span class="font-mono text-xs">{{ currentGroupDn }}</span>
        </div>

        <div class="flex-1 overflow-hidden w-full py-2 flex justify-center">
          <el-transfer
            v-model="targetMembers"
            filterable
            :titles="['系统内所有人员', '已加入该组的人员']"
            :button-texts="['移出', '加入']"
            :filter-method="filterMethod"
            filter-placeholder="姓名或账号缩写搜索"
            :data="allUserOptions"
            class="custom-transfer h-full"
          >
            <template #default="{ option }">
               <div class="text-xs">
                 <div class="font-medium">{{ option.displayName }}</div>
                 <div class="text-gray-400 font-mono scale-90 origin-left">{{ option.username }}</div>
               </div>
            </template>
          </el-transfer>
        </div>

        <div class="mt-8 flex justify-end">
           <el-button @click="drawerVisible = false">放弃并关闭</el-button>
           <el-button type="primary" @click="doUpdateGroupMembers" :loading="updatingMembers">
             执行覆盖组策略名单
           </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const loading = ref(false)
const groups = ref<string[]>([])
const searchQuery = ref('')

const fetchGroups = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/ad/groups')
    groups.value = data.groups || []
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '拉取安全组失败')
  } finally {
    loading.value = false
  }
}

// 所有用户的字典源 (为了 Transfer 左侧填充用)
interface UserOption { key: string; label: string; disabled?: boolean; displayName: string; username: string; }
const allUserOptions = ref<UserOption[]>([])

// 并发请求拿系统所有人员
const fetchAllUsers = async () => {
    try {
        const { data } = await axios.get('/api/ad/users', { params: { keyword: '' } }) 
        const rawUsers = data.users || []
        allUserOptions.value = rawUsers.map((u: any) => ({
             key: (u.dn || '').toLowerCase(),
             label: `${u.display_name} (${u.username})`,
             displayName: u.display_name,
             username: u.username,
             disabled: false
        }))
    } catch {
        ElMessage.warning('拉取全局人员字典失败，穿梭框内容可能不全')
    }
}

// 提取 CN
const extractCN = (dn: string) => {
  if (!dn) return ''
  const parts = dn.split(',')
  if (parts.length > 0 && typeof parts[0] === 'string' && parts[0].startsWith('CN=')) {
    return parts[0].substring(3)
  }
  return dn
}

const filteredGroups = computed(() => {
  if (!searchQuery.value) return groups.value
  const lowerQuery = searchQuery.value.toLowerCase()
  return groups.value.filter(g => g.toLowerCase().includes(lowerQuery))
})

onMounted(() => {
  fetchGroups()
  fetchAllUsers()
})

// ----- 抽屉与成员管理逻辑 -----
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentGroupDn = ref('')

const originMembers = ref<string[]>([])
const targetMembers = ref<string[]>([])
const updatingMembers = ref(false)

const filterMethod = (query: string, item: Record<string, any>) => {
  if (!item || typeof item.label !== 'string') return false
  return item.label.toLowerCase().includes(query.toLowerCase())
}

const openGroupDetail = async (groupDn: string) => {
    drawerVisible.value = true
    currentGroupDn.value = groupDn
    detailLoading.value = true
    
    originMembers.value = []
    targetMembers.value = []
    
    try {
        const { data } = await axios.post('/api/ad/group-members/list', {
             group_dn: groupDn
        })
        const members = data.members || []
        const lowerMembers = members.map((m: string) => m.toLowerCase())
        
        // 确保如果有不在左边大全集里的人员，要为它临时创建一条填充条目，只有这样 el-transfer 右侧才会渲染该选项
        lowerMembers.forEach((m: string) => {
            const exists = allUserOptions.value.some((o: UserOption) => o && o.key === m)
            if (!exists) {
                const cnName = m.split(',')[0]
                const safeCnName = cnName ? cnName.replace('CN=', '').replace('cn=', '') : m
                allUserOptions.value.push({
                     key: m,
                     label: m,
                     displayName: safeCnName,
                     username: '系统内建/不可见对象',
                     disabled: false
                })
            }
        })
        
        originMembers.value = [...lowerMembers]
        targetMembers.value = [...lowerMembers]
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '拉取安全组当前人员名单失败')
    } finally {
        detailLoading.value = false
    }
}

const doUpdateGroupMembers = async () => {
    updatingMembers.value = true
    try {
        await axios.put('/api/ad/group-members/update', {
             group_dn: currentGroupDn.value,
             old_members: originMembers.value,
             new_members: targetMembers.value
        })
        ElMessage.success('安全组人员更新成功！AD 已同步')
        originMembers.value = [...targetMembers.value]
        drawerVisible.value = false
    } catch (err: any) {
         ElMessage.error(err.response?.data?.detail || '安全组人员更新执行失败')
    } finally {
         updatingMembers.value = false
    }
}
</script>

<style scoped>
/* 动态穿梭框大小，使用 flex 模型自适应撑满剩余屏幕高度 */
:deep(.custom-transfer) {
  display: flex;
  align-items: center;
  height: 100%;
}
:deep(.custom-transfer .el-transfer-panel) {
  width: 360px;
  height: 100% !important;
  display: flex;
  flex-direction: column;
}
:deep(.custom-transfer .el-transfer-panel__body) {
  flex: 1;
  height: auto !important;
}
:deep(.custom-transfer .el-transfer-panel__list) {
  height: 100% !important;
}
:deep(.custom-transfer .el-transfer__buttons) {
  display: flex !important;
  flex-direction: column;
  justify-content: center;
  padding: 0 20px;
  gap: 15px;
}
/* 解决按钮堆叠时原生带来的侧移偏移问题 */
:deep(.custom-transfer .el-transfer__buttons .el-button) {
  margin: 0 !important;
  display: block;
}
</style>
