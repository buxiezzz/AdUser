<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">IT 资产台账与全生命周期管控</h1>
      <el-button type="primary" :icon="Plus" @click="openCreateDrawer">资产录入登记</el-button>
    </div>

    <!-- 顶层汇总状态卡片 / 过滤器 -->
    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <div class="flex flex-wrap gap-4 mb-6">
        <el-input v-model="searchKeyword" placeholder="检索资产编号、品牌、或使用者姓名..." prefix-icon="Search" class="w-80" clearable />
        <el-select v-model="searchStatus" placeholder="按资产状态筛选" clearable class="w-40" >
          <el-option label="在库" value="在库" />
          <el-option label="借用中" value="借用中" />
          <el-option label="维修中" value="维修中" />
          <el-option label="已报废" value="已归档/报废" />
        </el-select>
        <el-select v-model="searchCategory" placeholder="按设备分类筛选" clearable class="w-40" >
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button @click="fetchAssets" :icon="Refresh">刷新台账</el-button>
        <el-button type="success" :icon="Download" @click="exportExcel">导出台账(Excel)</el-button>
      </div>

      <el-table :data="filteredAssets" style="width: 100%" v-loading="loading" border stripe>
         <el-table-column prop="asset_code" label="固定资产编号" width="180">
            <template #default="{ row }">
              <span class="font-mono font-medium text-indigo-700">{{ row.asset_code || '未分配编号' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="设备分类" width="150">
           <template #default="{ row }">
             <el-tag size="small" type="info">{{ getCategoryName(row.category_id) }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="当前状态" width="120">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="当前持有人 / 责任人" width="200">
           <template #default="{ row }">
             <div v-if="row.owner" class="flex items-center space-x-2">
                <el-avatar size="small" class="bg-indigo-100 text-indigo-800">{{ row.owner.name.charAt(0) }}</el-avatar>
                <div class="flex flex-col">
                  <span class="text-sm font-medium leading-none">{{ row.owner.name }}</span>
                  <span class="text-xs text-gray-400 mt-1">{{ row.owner.department || row.owner.ad_account }}</span>
                </div>
             </div>
             <span v-else class="text-gray-400 text-sm">-</span>
           </template>
         </el-table-column>
         <el-table-column 
            v-for="key in dynamicHeaders" 
            :key="key" 
            :label="key"
            min-width="120"
            show-overflow-tooltip
          >
            <template #default="{ row }">
               <span class="text-gray-600">{{ row.dynamic_attributes ? row.dynamic_attributes[key] : '' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="操作管控" width="180" fixed="right">
           <template #default="{ row }">
             <el-button link type="primary" size="small" @click="openManageDrawer(row)">
               管理/调拨
             </el-button>
             <el-button link type="info" size="small" @click="openLogs(row)">
               追溯日志
             </el-button>
           </template>
         </el-table-column>
      </el-table>
    </el-card>

    <!-- 侧边栏资产抽屉(新建/维护) -->
    <el-drawer
      v-model="drawerVisible"
      :title="isNew ? '新资产入库登记' : `资产档案与流转: ${currentAsset?.asset_code || '未命名'}`"
      size="650px"
      append-to-body
      destroy-on-close
    >
      <div v-loading="submitLoading" class="px-4 pb-12">
        <el-form label-position="top">
          <!-- 基础信息 -->
          <div class="grid grid-cols-2 gap-4">
            <el-form-item label="固资入账编号" required>
              <el-input v-model="form.asset_code" placeholder="如 IT-PC-2023001" />
            </el-form-item>
            <el-form-item label="设备分类" required>
              <el-select v-model="form.category_id" placeholder="选择资产类型" @change="handleCategoryChange">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <el-form-item label="当前资产状态" required>
              <el-select v-model="form.status" placeholder="流转状态" @change="handleStatusChange">
                <el-option label="在库" value="在库" />
                <el-option label="借用中" value="借用中" />
                <el-option label="维修中" value="维修中" />
                <el-option label="已归档/报废" value="已归档/报废" />
              </el-select>
            </el-form-item>
            <el-form-item label="资产挂载/使用人" class="flex-1">
              <el-select
                v-model="form.owner_id"
                filterable
                remote
                clearable
                placeholder="键入检索 AD/本地员工"
                :remote-method="searchEmployees"
                :loading="empLoading"
                :disabled="form.status === '在库' || form.status === '已归档/报废'"
              >
                <el-option
                  v-for="emp in employees"
                  :key="emp.id"
                  :label="`${emp.name} (${emp.ad_account || '本地'})`"
                  :value="emp.id"
                >
                  <span style="float: left">{{ emp.name }}</span>
                  <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">{{ emp.department }}</span>
                </el-option>
              </el-select>
              <div v-if="form.status === '在库' || form.status === '已归档/报废'" class="text-xs text-gray-400 mt-1">在库或报废状态下，资产将强制收回且无法绑定使用人。</div>
            </el-form-item>
          </div>

          <el-divider>业务扩展属性 (JSONB 动态渲染)</el-divider>
          
          <div v-if="Object.keys(form.dynamic_attributes).length > 0" class="bg-gray-50 border rounded-lg p-4 space-y-4">
            <el-form-item 
              v-for="(typeDesc, key) in currentCatTpl" 
              :key="key" 
              :label="`${key} ${typeDesc ? '('+typeDesc+')' : ''}`"
            >
               <el-input v-model="form.dynamic_attributes[key]" :placeholder="`输入${key}`" />
            </el-form-item>
          </div>
          <div v-else class="text-sm text-gray-400 text-center py-4 bg-gray-50 rounded-lg">
            尚未选择分类或该分类下无预设的动态模板字典。
          </div>

          <div class="mt-8 flex justify-end space-x-3">
            <el-button @click="drawerVisible = false">取消放弃</el-button>
            <el-button type="danger" plain v-if="!isNew && form.status !== '已归档/报废'" @click="doArchive">强制报废拆除</el-button>
            <el-button type="primary" @click="submitSave">保存提交台账</el-button>
          </div>
        </el-form>
      </div>
    </el-drawer>

    <!-- 日志追溯弹层 -->
    <el-dialog v-model="logVisible" :title="`资产追溯审计: ${currentAsset?.asset_code || ''}`" width="600px">
       <div v-loading="logLoading" class="min-h-[200px] px-4">
         <el-timeline v-if="logs.length > 0" class="mt-4">
            <el-timeline-item
              v-for="log in logs"
              :key="log.id"
              :timestamp="new Date(log.created_at).toLocaleString()"
              :type="log.action.includes('新建') ? 'success' : 'primary'"
            >
              <div class="text-sm">
                <span class="font-medium text-gray-800">{{ log.action }}</span>
                <span class="text-xs text-gray-500 ml-2"><el-icon><User /></el-icon> {{ log.operator_name }}</span>
                <div v-if="log.previous_owner_name || log.new_owner_name" class="text-xs mt-1 text-blue-600 font-medium flex items-center space-x-1">
                   <span>[{{ log.previous_owner_name || '无归属' }}]</span>
                   <el-icon><Right /></el-icon>
                   <span>[{{ log.new_owner_name || '无归属' }}]</span>
                </div>
                <div class="text-xs mt-2 text-gray-500 bg-gray-50 p-2 rounded border">{{ log.memo }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无追溯记录" />
       </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Refresh, Download, User, Right } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'

const loading = ref(false)
const rawAssets = ref<any[]>([])
const categories = ref<any[]>([])
const employees = ref<any[]>([])
const empLoading = ref(false)

const searchKeyword = ref('')
const searchStatus = ref('')
const searchCategory = ref<number | ''>('')

const fetchGlobals = async () => {
    try {
        const [catRes, empRes] = await Promise.all([
            axios.get('/api/assets/categories'),
            axios.get('/api/assets/employees', { params: { keyword: '' }}) 
        ])
        categories.value = catRes.data || []
        employees.value = empRes.data || []
    } catch {
        ElMessage.warning('拉取分类与人员基础数据失败')
    }
}

const fetchAssets = async () => {
    loading.value = true
    try {
        const { data } = await axios.get('/api/assets/')
        rawAssets.value = data || []
    } catch {
        ElMessage.error('无法拉取资产池数据')
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchGlobals()
    fetchAssets()
})

const filteredAssets = computed(() => {
    return rawAssets.value.filter(a => {
        let matchKw = true
        let matchSt = true
        let matchCat = true
        
        if (searchKeyword.value) {
            const kw = searchKeyword.value.toLowerCase()
            const code = (a.asset_code || '').toLowerCase()
            const ownerName = a.owner ? a.owner.name.toLowerCase() : ''
            matchKw = code.includes(kw) || ownerName.includes(kw)
        }
        if (searchStatus.value) {
            matchSt = a.status === searchStatus.value
        }
        if (searchCategory.value !== '') {
            matchCat = a.category_id === searchCategory.value
        }
        return matchKw && matchSt && matchCat
    })
})

const dynamicHeaders = computed(() => {
    const keys = new Set<string>()
    filteredAssets.value.forEach(asset => {
        if(asset.dynamic_attributes) {
            Object.keys(asset.dynamic_attributes).forEach(k => keys.add(k))
        }
    })
    return Array.from(keys)
})

const getCategoryName = (id: number) => {
    const c = categories.value.find(x => x.id === id)
    return c ? c.name : '未知分类'
}

const getStatusType = (status: string) => {
    if(status === '在库') return 'success'
    if(status === '借用中') return 'primary'
    if(status === '维修中') return 'warning'
    return 'danger' // 报废
}

// ------ 抽屉功能 ------
const drawerVisible = ref(false)
const isNew = ref(true)
const submitLoading = ref(false)
const currentAsset = ref<any>(null)
const logs = ref<any[]>([])

// 为了演示，这里的人员搜索暂时在刚才拉的假数据里找，如果需要从AD实时搜索可以通过改造下面这块。
const searchEmployees = async (query: string) => {
    if (!query) return;
    empLoading.value = true
    try {
       const { data } = await axios.get('/api/assets/employees', { params: { keyword: query } }) 
       employees.value = data || []
    } finally {
       empLoading.value = false
    }
}

const form = ref<any>({
    asset_code: '',
    category_id: undefined,
    status: '在库',
    owner_id: undefined,
    dynamic_attributes: {}
})

const currentCatTpl = computed(() => {
    if(!form.value.category_id) return {}
    const c = categories.value.find(x => x.id === form.value.category_id)
    return c?.default_attributes || {}
})

const handleCategoryChange = (_val: number) => {
    if(isNew.value) {
        // 重置动态表单并填入 key
        const tpl = currentCatTpl.value
        const dict: any = {}
        Object.keys(tpl).forEach(k => dict[k] = '')
        form.value.dynamic_attributes = dict
    }
}

const handleStatusChange = (val: string) => {
    if(val === '在库' || val === '已归档/报废') {
        form.value.owner_id = undefined
    }
}

const openCreateDrawer = () => {
    isNew.value = true
    currentAsset.value = null
    logs.value = []
    form.value = {
        asset_code: '',
        category_id: undefined,
        status: '在库',
        owner_id: undefined,
        dynamic_attributes: {}
    }
    drawerVisible.value = true
}

const openManageDrawer = async (row: any) => {
    isNew.value = false
    currentAsset.value = row
    form.value = {
        asset_code: row.asset_code,
        category_id: row.category_id,
        status: row.status,
        owner_id: row.owner_id,
        dynamic_attributes: { ...row.dynamic_attributes }
    }
    
    // 补齐缺失的字段模板
    const tplKeys = Object.keys(currentCatTpl.value)
    tplKeys.forEach(k => {
        if(form.value.dynamic_attributes[k] === undefined) {
            form.value.dynamic_attributes[k] = ''
        }
    })
    
    drawerVisible.value = true
}

const logVisible = ref(false)
const logLoading = ref(false)
const openLogs = async (row: any) => {
    currentAsset.value = row
    logVisible.value = true
    logLoading.value = true
    try {
        const { data } = await axios.get(`/api/assets/${row.id}/logs`)
        logs.value = data || []
    } catch {
        ElMessage.warning('拉取审计流水失败')
    } finally {
        logLoading.value = false
    }
}

const submitSave = async () => {
    if(!form.value.asset_code || !form.value.category_id) {
        return ElMessage.warning('编号与分类为必填项')
    }
    submitLoading.value = true
    try {
        if(isNew.value) {
            await axios.post('/api/assets/', form.value)
            ElMessage.success('初次登记入库成功')
        } else {
            await axios.put(`/api/assets/${currentAsset.value.id}`, form.value)
            ElMessage.success('配置流转与修改成功')
        }
        drawerVisible.value = false
        fetchAssets()
    } catch(err:any) {
        ElMessage.error(err.response?.data?.detail || '保存失败')
    } finally {
        submitLoading.value = false
    }
}

const doArchive = async () => {
    try {
        await ElMessageBox.confirm('确定要将该资产强制作废并强制出库吗？该操作将被详细审计记录且通常不可逆！', '作废警报', { type: 'error'})
    } catch { return }
    
    submitLoading.value = true
    try {
        await axios.delete(`/api/assets/${currentAsset.value.id}`)
        ElMessage.success('成功置为报废状态并审计')
        drawerVisible.value = false
        fetchAssets()
    } catch(err:any) {
        ElMessage.error(err.response?.data?.detail || '作废执行失败')
    } finally {
        submitLoading.value = false
    }
}

const exportExcel = () => {
    if (filteredAssets.value.length === 0) return ElMessage.warning('当前暂无数据可导出')
    
    const rows = filteredAssets.value.map(a => {
        const baseRow: any = {
            '资产编号': a.asset_code,
            '设备分类': getCategoryName(a.category_id),
            '当前状态': a.status,
            '当前持有人': a.owner ? a.owner.name : '闲置',
            '持有人部门': a.owner ? a.owner.department : '-',
            '入库时间': new Date(a.created_at).toLocaleString()
        }
        
        dynamicHeaders.value.forEach(h => {
             baseRow[h] = a.dynamic_attributes ? (a.dynamic_attributes[h] || '') : ''
        })
        
        return baseRow
    })

    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "资产台账导出")
    XLSX.writeFile(wb, `IT资产台账导出_${new Date().getTime()}.xlsx`)
}
</script>
