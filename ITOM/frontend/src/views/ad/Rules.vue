<template>
  <div class="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-top-4 duration-700">
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div class="flex flex-col space-y-2">
        <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">AD 命名规范中心</h1>
        <p class="text-gray-500 text-lg">
          基于当前已定义的部门标识与职位标识，系统将遵循：<code>{部门}-{职位}-{姓名}</code> 自动生成账号描述。
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <el-button @click="navigateToTemplates" plain>去管理权限映射</el-button>
        <el-button type="primary" :loading="saving" :icon="Check" @click="saveUnifiedRules">保存标识更动</el-button>
      </div>
    </div>

    <!-- 交互预览区 -->
    <el-card shadow="never" class="border-0 ring-1 ring-indigo-50 rounded-3xl bg-gradient-to-br from-indigo-50/40 to-white overflow-hidden shadow-xl">
      <div class="flex flex-col md:flex-row p-4 gap-8">
        <div class="flex-1 space-y-4">
          <h3 class="text-lg font-bold text-dark flex items-center">
             <el-icon class="mr-2"><MagicStick /></el-icon> 账号生成即时预览
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
             <el-form-item label="测试姓名">
               <el-input v-model="previewName" placeholder="输入姓名，如: 张三" />
             </el-form-item>
             <el-form-item label="模拟部门">
               <el-select v-model="previewOU" placeholder="选择部门" class="w-full">
                 <el-option v-for="(prefix, dn) in ouPrefixMapping" :key="dn" :label="simplifyDN(dn)" :value="prefix" />
               </el-select>
             </el-form-item>
             <el-form-item label="模拟职位">
               <el-select v-model="previewPos" placeholder="选择职位" class="w-full">
                 <el-option v-for="pos in positionsData" :key="pos.name" :label="pos.name" :value="pos.suffix" />
               </el-select>
             </el-form-item>
          </div>
        </div>
        <div class="w-full md:w-80 flex flex-col items-center justify-center bg-white rounded-2xl border-2 border-dashed border-indigo-100 p-6">
          <span class="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-2">生成后的 AD Description</span>
          <div class="text-2xl font-black text-primary break-all text-center">
            {{ previewName ? `${previewOU || 'AA'}-${previewPos || 'BB'}-${previewName}` : '等待输入姓名...' }}
          </div>
        </div>
      </div>
    </el-card>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- 部门标识管理 -->
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-bold text-gray-800 flex items-center">
            <el-icon class="mr-2 text-primary"><OfficeBuilding /></el-icon> 部门标识 (AA)
          </h3>
        </div>
        <el-table :data="ouList" border class="rounded-2xl overflow-hidden shadow-sm" stripe>
          <el-table-column label="组织单元 (OU路径)" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="text-sm font-medium">{{ simplifyDN(row.dn) }}</span>
              <div class="text-[10px] text-gray-400 truncate">{{ row.dn }}</div>
            </template>
          </el-table-column>
          <el-table-column label="映射代码" width="140">
            <template #default="{ row }">
              <el-input v-model="row.prefix" size="small" placeholder="如: RD" class="uppercase" />
            </template>
          </el-table-column>
        </el-table>
        <div class="text-[10px] text-gray-400 text-center">注：部门标识优先继承父级 OU 配置</div>
      </section>

      <!-- 职位标识管理 -->
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-bold text-gray-800 flex items-center">
            <el-icon class="mr-2 text-primary"><UserFilled /></el-icon> 职位标识 (BB)
          </h3>
        </div>
        <el-table :data="positionsData" border class="rounded-2xl overflow-hidden shadow-sm" stripe>
          <el-table-column prop="name" label="职位全称">
            <template #default="{ row }">
               <span class="font-bold">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="映射代码" width="140">
            <template #default="{ row }">
              <el-input v-model="row.suffix" size="small" placeholder="如: SE" />
            </template>
          </el-table-column>
        </el-table>
        <div class="text-[10px] text-gray-400 text-center">修改职位名称及权限请进入“权限模板配置”</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { MagicStick, Check, OfficeBuilding, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const saving = ref(false)
const loading = ref(false)

// 核心数据 (与 Templates.vue 共享)
const ouPrefixMapping = ref<Record<string, string>>({})
const positionsData = ref<any[]>([])

// 为了表格展示，将 Mapping 转为 List
const ouList = ref<any[]>([])

// 预览用
const previewName = ref('')
const previewOU = ref('')
const previewPos = ref('')

const fetchData = async () => {
  loading.value = true
  try {
    const { data: config } = await axios.get('/api/settings/')
    ouPrefixMapping.value = config.OU_PREFIX_MAPPING || {}
    positionsData.value = config.POSITIONS || []
    
    // 初始化表格
    ouList.value = Object.entries(ouPrefixMapping.value).map(([dn, prefix]) => ({
      dn, prefix
    }))
    
    // 初始化预览选项
    if (ouList.value.length > 0) previewOU.value = ouList.value[0].prefix
    if (positionsData.value.length > 0) previewPos.value = positionsData.value[0].suffix
    
  } catch {
    ElMessage.error('加载系统配置失败')
  } finally {
    loading.value = false
  }
}

const simplifyDN = (dn: string) => {
  return dn.split(',').find(p => p.startsWith('OU='))?.replace('OU=', '') || dn
}

const navigateToTemplates = () => {
  router.push('/settings/templates')
}

const saveUnifiedRules = async () => {
  saving.value = true
  try {
    // 逆向回写
    const newPrefixMap: Record<string, string> = {}
    ouList.value.forEach(row => {
      newPrefixMap[row.dn] = row.prefix
    })
    
    // 构造 payload (部分更新逻辑)
    const payload = {
      ou_prefix_mapping: newPrefixMap,
      positions: positionsData.value
    }
    
    const { data } = await axios.post('/api/settings/', payload)
    if (data.success) {
      ElMessage.success('命名规则已全站同步生效')
    }
  } catch {
    ElMessage.error('同步失败')
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
:deep(.el-card) {
  border: none;
}
</style>

