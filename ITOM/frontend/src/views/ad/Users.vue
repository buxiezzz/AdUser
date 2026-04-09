<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">域用户检索与管理</h1>
    </div>

    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl relative">
      <div class="flex items-center space-x-4 mb-6">
        <el-input 
          v-model="keyword" 
          placeholder="输入账号名或显示名称进行模糊搜索" 
          prefix-icon="Search"
          class="w-80"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch" :loading="loading">
          在 AD 域中查找
        </el-button>
        <el-button type="success" plain :icon="Download" @click="handleExport" :loading="exporting">
          导出域用户名单 (Excel)
        </el-button>
      </div>
      
      <el-table :data="displayUsers" style="width: 100%" v-loading="loading" border stripe>
         <el-table-column prop="display_name" label="显示名称" min-width="150" />
         <el-table-column prop="username" label="登录账号" min-width="150" />
         <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
           <template #default="{ row }">
             <span class="text-gray-600">{{ row.description || '-' }}</span>
           </template>
         </el-table-column>
         <el-table-column prop="upn" label="UPN 邮箱别名" min-width="250" />
         <el-table-column label="账号状态" width="100">
           <template #default="{ row }">
             <el-tag :type="row.enabled ? 'success' : 'danger'" size="small">
               {{ row.enabled ? '正常' : '已禁用' }}
             </el-tag>
           </template>
         </el-table-column>
         <el-table-column label="操作" width="120" fixed="right">
           <template #default="{ row }">
             <el-button link type="primary" size="small" @click="openUserDetail(row)">
               详情与修改
             </el-button>
           </template>
         </el-table-column>
      </el-table>
      
      <div class="mt-6 flex justify-between items-center" v-if="users.length > 0">
        <span class="text-sm text-gray-500 font-medium">共检索到 <span class="text-indigo-600 font-bold">{{ users.length }}</span> 名员工</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="users.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          background
          class="is-background"
        />
      </div>
    </el-card>

    <!-- 详情侧边栏抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`编辑员工资料: ${currentUser?.display_name || '-'}`"
      size="600px"
      append-to-body
    >
      <div v-loading="detailLoading" class="space-y-6 px-2">
        <!-- 基础信息区 -->
        <div class="bg-gray-50 p-4 rounded-lg space-y-2">
          <div class="flex items-center"><span class="w-24 text-gray-500 text-sm">登录名:</span> <span class="font-medium font-mono text-sm">{{ currentUser?.username }}</span></div>
          <div class="flex items-center"><span class="w-24 text-gray-500 text-sm">DN 路径:</span> <span class="text-gray-600 font-mono text-xs break-all leading-tight">{{ currentUser?.dn }}</span></div>
          <div class="flex items-center pt-2">
            <span class="w-24 text-gray-500 text-sm">账号状态:</span>
            <el-tag :type="currentUser?.enabled ? 'success' : 'danger'" size="small">
              {{ currentUser?.enabled ? '正常激活' : '已禁用' }}
            </el-tag>
            <el-button 
              class="ml-auto" 
              :type="currentUser?.enabled ? 'danger' : 'success'" 
              size="small" 
              plain
              :loading="togglingStatus"
              @click="doToggleStatus"
            >
              {{ currentUser?.enabled ? '立即禁用该账号' : '激活并启用账号' }}
            </el-button>
          </div>
        </div>

        <el-divider>安全与变更</el-divider>

        <!-- 密码修改 -->
        <el-form label-position="top">
          <el-form-item label="强制重置域密码">
            <div class="flex space-x-2 w-full">
               <el-input v-model="newPassword" show-password placeholder="输入新密码并牢记" />
               <el-button type="danger" plain @click="doUpdatePassword" :loading="updatingPwd">变更密码</el-button>
            </div>
            <div class="text-xs text-gray-400 mt-1">此操作直接覆写 AD 中的密码，请确保满足域强密码策略。</div>
          </el-form-item>

          <!-- 部门转移 -->
          <el-form-item label="所属组织单元 (OU)" class="mt-5">
            <div class="flex items-center w-full space-x-2">
              <el-select v-model="selectedOu" filterable placeholder="选择新的部门级别 OU (将平滑迁移)" class="flex-1">
                <el-option v-for="ou in ouOptions" :key="ou.dn" :label="ou.name" :value="ou.dn" />
              </el-select>
              <el-button type="warning" plain @click="doUpdateOU" :loading="updatingOu">转移部门</el-button>
            </div>
          </el-form-item>

          <!-- 安全组修改 -->
          <el-form-item label="隶属的安全组权限 (MemberOf)" class="mt-5">
            <el-select
              v-model="selectedGroups"
              multiple
              filterable
              placeholder="添加或移除用户的安全组"
              style="width: 100%"
            >
              <el-option v-for="group in allGroups" :key="group" :label="group" :value="group" />
            </el-select>
            <el-button type="primary" class="mt-3 w-full" @click="doUpdateGroups" :loading="updatingGroups">
              保存安全组更改
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Search, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const keyword = ref('')
const loading = ref(false)
const users = ref<any[]>([])
const exporting = ref(false)

// 分页逻辑
const currentPage = ref(1)
const pageSize = ref(20)

const displayUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return users.value.slice(start, end)
})

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 预加载的全局可选项
const ouOptions = ref<{dn: string, name: string}[]>([])
const allGroups = ref<string[]>([])

const fetchGlobalOptions = async () => {
    try {
        const [{ data: ous }, { data: grps }] = await Promise.all([
             axios.get('/api/ad/ous'),
             axios.get('/api/ad/groups')
        ])
        ouOptions.value = ous
        allGroups.value = grps.groups || []
    } catch (e: any) {
        console.error('拉取选项字典失败', e)
    }
}

onMounted(() => {
    fetchGlobalOptions()
})

const handleSearch = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/ad/users', { 
      params: { keyword: keyword.value } 
    })
    users.value = data.users || []
    currentPage.value = 1 // 搜索后重置到第一页
    if (users.value.length === 0) {
      ElMessage.warning('未找到符合要求的域用户')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '搜索用户发生异常')
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const response = await axios.get('/api/ad/users/export', {
      params: { keyword: keyword.value },
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // 生成带时间戳的文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    link.setAttribute('download', `AD_Users_Export_${timestamp}.xlsx`)
    
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('域用户名单导出成功')
  } catch (err: any) {
    console.error('导出失败', err)
    ElMessage.error('导出 Excel 失败，请检查网络或权限')
  } finally {
    exporting.value = false
  }
}

// ---------------- 抽屉与编辑逻辑 ----------------
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentUser = ref<any>(null)

// 变更表单所绑定的状态
const newPassword = ref('')
const updatingPwd = ref(false)

const selectedOu = ref('')
const updatingOu = ref(false)

const originGroups = ref<string[]>([])
const selectedGroups = ref<string[]>([])
const updatingGroups = ref(false)

const togglingStatus = ref(false)

const openUserDetail = async (row: any) => {
    drawerVisible.value = true
    detailLoading.value = true
    currentUser.value = row
    
    // 初始化空状态
    newPassword.value = ''
    selectedOu.value = '' // 获取真正的 OU DN 是个比较复杂的操作，通常是从用户 DN 倒推。为避免复杂的字符串操作，直接让选新的。
    selectedGroups.value = []
    originGroups.value = []
    
    // 尝试找出它的当前 OU，根据 DN 剥除前面的 CN=Name,
    if (row.dn) {
        const parts = row.dn.split(',')
        if (parts.length > 1 && parts[0].startsWith('CN=')) {
           selectedOu.value = parts.slice(1).join(',')
        }
    }

    try {
        const { data } = await axios.get(`/api/ad/users/${row.username}`)
        const detail = data.user
        currentUser.value = detail
        
        originGroups.value = [...(detail.groups || [])]
        selectedGroups.value = [...(detail.groups || [])]
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '拉取用户详细属性失败')
    } finally {
        detailLoading.value = false
    }
}

const doUpdatePassword = async () => {
    if (!newPassword.value || newPassword.value.length < 5) {
        return ElMessage.warning('输入的新密码太短')
    }
    
    try {
        await ElMessageBox.confirm('确定要为该员工重置密码吗?', '警告', { type: 'warning' })
    } catch { return }

    updatingPwd.value = true
    try {
        await axios.put(`/api/ad/users/${currentUser.value.username}/password`, {
            user_dn: currentUser.value.dn,
            new_password: newPassword.value
        })
        ElMessage.success('用户密码重置成功')
        newPassword.value = ''
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '密码变更失败')
    } finally {
        updatingPwd.value = false
    }
}

const doUpdateOU = async () => {
    if (!selectedOu.value) return ElMessage.warning('请选择目标转移部门')
    updatingOu.value = true
    try {
        await axios.put(`/api/ad/users/${currentUser.value.username}/ou`, {
            user_dn: currentUser.value.dn,
            new_ou_dn: selectedOu.value
        })
        ElMessage.success('部门组织关系转移成功')
        // 伪刷新当前列表项的 DN 展示
        const cnPart = currentUser.value.dn.split(',')[0]
        currentUser.value.dn = `${cnPart},${selectedOu.value}`
        // 同步修改表格里显示的值
        const index = users.value.findIndex(u => u.username === currentUser.value.username)
        if (index > -1) { users.value[index].dn = currentUser.value.dn }
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '部门转移失败')
    } finally {
        updatingOu.value = false
    }
}

const doUpdateGroups = async () => {
    updatingGroups.value = true
    try {
        await axios.put(`/api/ad/users/${currentUser.value.username}/groups`, {
            user_dn: currentUser.value.dn,
            old_groups: originGroups.value,
            new_groups: selectedGroups.value
        })
        ElMessage.success('所属安全组更新完成')
        originGroups.value = [...selectedGroups.value]
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '安全组更新失败')
    } finally {
        updatingGroups.value = false
    }
}

const doToggleStatus = async () => {
    const actionText = currentUser.value.enabled ? '禁用' : '启用'
    try {
        await ElMessageBox.confirm(`确定要${actionText}域账号 [${currentUser.value.username}] 吗?`, '警告', {
            type: 'warning',
            confirmButtonText: `确认${actionText}`,
            cancelButtonText: '取消'
        })
    } catch { return }

    togglingStatus.value = true
    try {
        const targetEnabled = !currentUser.value.enabled
        await axios.put(`/api/ad/users/${currentUser.value.username}/status`, {
            user_dn: currentUser.value.dn,
            enabled: targetEnabled
        })
        ElMessage.success(`用户已成功${actionText}`)
        // 同步更新本地状态
        currentUser.value.enabled = targetEnabled
        const idx = users.value.findIndex(u => u.username === currentUser.value.username)
        if (idx > -1) {
            users.value[idx].enabled = targetEnabled
        }
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '状态切换失败')
    } finally {
        togglingStatus.value = false
    }
}
</script>
