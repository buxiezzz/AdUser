<template>
  <div class="space-y-6 pb-20">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">参数配置</h1>
      <el-button type="primary" :loading="saving" @click="saveTemplates">
        <el-icon class="mr-1"><Check /></el-icon>
        保存所有配置
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <!-- OU 关联默认安全组 -->
      <el-tab-pane label="OU 默认安全组映射" name="ou_groups">
        <div class="mb-4 flex justify-between items-center">
          <div class="text-sm text-gray-500">
            当管理员通过向导开通特定 OU 下的用户时，系统将自动带入并勾选在此处配置的安全组。
          </div>
          <el-button size="small" type="primary" plain @click="openAddOUDialog">
            + 添加 OU 映射
          </el-button>
        </div>
        
        <el-table :data="ouTableData" style="width: 100%" v-loading="loading" border stripe>
          <el-table-column prop="name" label="组织单元 (OU)" width="300">
            <template #default="{ row }">
              <span class="font-medium text-gray-700">{{ row.name }}</span>
              <div class="text-xs text-gray-400 mt-1" style="word-break: break-all;">{{ row.dn }}</div>
            </template>
          </el-table-column>
          <el-table-column label="部门标识 (AA)" width="150">
            <template #default="{ row }">
              <el-input v-model="row.prefix" placeholder="如: TECH" />
            </template>
          </el-table-column>
          <el-table-column label="绑定的默认安全组">
            <template #default="{ row }">
              <el-select
                v-model="row.default_groups"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="请选择或输入要绑定的安全组"
                style="width: 100%"
              >
                <el-option
                  v-for="group in groupOptions"
                  :key="group"
                  :label="group"
                  :value="group"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ $index }">
              <el-button type="danger" circle size="small" @click="removeOUMapping($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 职位关联默认安全组 -->
      <el-tab-pane label="职位/岗位配置" name="positions">
        <div class="mb-4 text-sm text-gray-500 flex justify-between items-center">
          <span>在此统一定义公司可用职位，并为每个职位绑定其缺省的安全组权限。</span>
          <el-button size="small" type="primary" plain @click="addPosition">
            + 添加新职位
          </el-button>
        </div>

        <el-table :data="positionList" style="width: 100%" v-loading="loading" border stripe>
          <el-table-column prop="name" label="职位名称" width="200">
            <template #default="{ row }">
              <el-input v-model="row.name" placeholder="如: 后端工程师" />
            </template>
          </el-table-column>
          <el-table-column prop="suffix" label="岗位标识/后缀" width="150">
            <template #default="{ row }">
              <el-input v-model="row.suffix" placeholder="如: backend" />
            </template>
          </el-table-column>
          <el-table-column label="职位独有的默认安全组">
            <template #default="{ row }">
              <el-select
                v-model="row.default_groups"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="请选择或输入该职位必配的安全组"
                style="width: 100%"
              >
                <el-option
                  v-for="group in groupOptions"
                  :key="group"
                  :label="group"
                  :value="group"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button type="danger" circle size="small" @click="removePosition($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 全局账号预设 -->
      <el-tab-pane label="全域默认配置" name="global_config">
        <div class="p-6 bg-gray-50/50 rounded-2xl border border-dashed border-gray-200 mt-4 space-y-6">
          <div class="flex items-center space-x-3 text-dark font-bold text-lg">
            <el-icon :size="24"><Lock /></el-icon>
            <span>域账号开通预设策略</span>
          </div>
          
          <div class="max-w-md">
            <el-form-item label="默认初始密码 (AD 密码策略)">
              <el-input 
                v-model="defaultPassword" 
                placeholder="设置全公司通用的初始化密码"
                show-password
              >
                <template #prefix><el-icon><Key /></el-icon></template>
              </el-input>
            </el-form-item>
            <p class="text-xs text-gray-400 mt-2">
              注意：请确保此密码符合 AD 域控的复杂度要求（长度、数字、特殊字符）。该设置将强制锁定“一键创建”模块的密码输入框。
            </p>
          </div>
        </div>
      </el-tab-pane>

      <!-- 地区过滤器整合 -->
      <el-tab-pane label="地区过滤器" name="region_filter">
        <div class="space-y-6 mt-4">
          <div class="flex justify-between items-end">
            <div class="space-y-1">
              <div class="text-sm font-bold text-gray-700">物理地区锁定</div>
              <div class="text-xs text-gray-400">选择一个当前工作的物理地区。系统将在创建账号时自动过滤 OU。</div>
            </div>
            <el-button :icon="Setting" size="small" @click="openManage">
              地区字典库管理
            </el-button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- “全域视图”卡片 -->
            <div 
              class="relative cursor-pointer transition-all duration-300"
              @click="selectRegion('all')"
            >
              <div 
                :class="[
                  'p-4 rounded-2xl border-2 transition-all duration-300 flex flex-col items-center text-center space-y-2',
                  activeRegionCode === 'all' 
                    ? 'border-primary bg-indigo-50/30' 
                    : 'border-gray-100 bg-white hover:border-indigo-100'
                ]"
              >
                <div :class="['p-3 rounded-xl', activeRegionCode === 'all' ? 'bg-primary text-white' : 'bg-gray-50 text-gray-400']">
                  <el-icon :size="24"><Monitor /></el-icon>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900 text-sm">全域策略视图</h4>
                  <p class="text-[10px] text-gray-400 mt-1 line-clamp-2">展示完整的 AD 原始数据。</p>
                </div>
                <div v-if="activeRegionCode === 'all'" class="absolute top-1 right-1">
                  <el-icon class="text-primary" :size="16"><CircleCheckFilled /></el-icon>
                </div>
              </div>
            </div>

            <!-- 动态地区卡片 -->
            <div 
              v-for="region in regions" 
              :key="region.code"
              class="relative cursor-pointer transition-all duration-300"
              @click="selectRegion(region.code)"
            >
              <div 
                :class="[
                  'p-4 rounded-2xl border-2 transition-all duration-300 flex flex-col items-center text-center space-y-2',
                  activeRegionCode === region.code 
                    ? 'border-emerald-500 bg-emerald-50/30' 
                    : 'border-gray-100 bg-white hover:border-emerald-100'
                ]"
              >
                <div :class="['p-3 rounded-xl', activeRegionCode === region.code ? 'bg-emerald-500 text-white' : 'bg-gray-50 text-gray-400']">
                  <el-icon :size="24"><Location /></el-icon>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900 text-sm">{{ region.name }}</h4>
                  <div class="flex flex-wrap justify-center gap-1 mt-1">
                    <el-tag 
                      v-for="kw in region.keywords" 
                      :key="kw" 
                      size="small" 
                      class="px-1 scale-75 origin-center"
                      :effect="activeRegionCode === region.code ? 'dark' : 'plain'"
                      :type="activeRegionCode === region.code ? 'success' : 'info'"
                    >
                      {{ kw }}
                    </el-tag>
                  </div>
                </div>
                <div v-if="activeRegionCode === region.code" class="absolute top-1 right-1">
                  <el-icon class="text-emerald-500" :size="16"><CircleCheckFilled /></el-icon>
                </div>
              </div>
            </div>
          </div>

        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加 OU 映射弹窗 -->
    <el-dialog v-model="addOUDialogVisible" title="添加 OU 映射" width="500px">
      <el-form label-width="120px">
        <el-form-item label="选择组织单元 (OU)">
          <el-select v-model="selectedOU" placeholder="请选择 OU" style="width: 100%" filterable>
            <el-option
              v-for="ou in availableOUs"
              :key="ou.dn"
              :label="ou.name"
              :value="ou.dn"
            >
              <span style="float: left">{{ ou.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">{{ simplifyOU(ou.dn) }}</span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addOUDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddOU" :disabled="!selectedOU">确认添加</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 地区字典管理弹窗 -->
    <el-dialog 
      v-model="manageVisible" 
      title="地区字典库管理" 
      width="700px" 
      destroy-on-close
    >
      <div class="space-y-6">
        <div class="flex justify-between items-center mb-4">
          <span class="text-gray-500 text-sm">定义业务覆盖的物理地区及其自动匹配关键词。</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd" circle />
        </div>

        <el-table :data="regionsList" border stripe>
          <el-table-column label="地区名称" width="150">
            <template #default="{ row }">
              <el-input v-model="row.name" placeholder="如: 北京" class="font-bold" />
            </template>
          </el-table-column>
          <el-table-column label="识别码" width="130">
            <template #default="{ row }">
              <el-input v-model="row.code" placeholder="如: beijing" />
            </template>
          </el-table-column>
          <el-table-column label="关键词 (以逗号分隔)">
            <template #default="{ row }">
              <el-input v-model="row.keywordStr" placeholder="匹配 AD 路径的关键字" @blur="syncKeywords(row)" />
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button :icon="Delete" type="danger" link @click="removeRegion($index)" />
            </template>
          </el-table-column>
        </el-table>

        <div class="bg-orange-50 p-4 rounded-xl flex items-start space-x-3">
          <el-icon class="text-orange-400 mt-0.5"><InfoFilled /></el-icon>
          <p class="text-xs text-orange-800 leading-relaxed">
            注意：删除一个正在使用的地区会导致全系统过滤器回退到“全域视图”。请在删除前确保已解除该地区的关联。
          </p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="manageVisible = false">取消</el-button>
          <el-button type="primary" :loading="updatingList" @click="saveRegionOptions">保存字典库</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Check, Delete, Lock, Key, Monitor, Location, CircleCheckFilled, Setting, Plus, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const activeTab = ref('ou_groups')
const loading = ref(false)
const saving = ref(false)

// Data Sources
const groupOptions = ref<string[]>([])
const ouList = ref<{dn: string, name: string}[]>([])

// V-Models for settings
// ouTableData will wrap the AD OU options with their current mapped default_groups & prefix
const ouTableData = ref<Array<{dn: string, name: string, default_groups: string[], prefix: string}>>([])
const positionList = ref<Array<{name: string, suffix: string, default_groups: string[]}>>([])
const defaultPassword = ref('')

// 地区过滤器数据状态
interface Region {
  code: string
  name: string
  keywords: string[]
  keywordStr?: string // 临时字段
}
const regions = ref<Region[]>([])
const activeRegionCode = ref('all')
const manageVisible = ref(false)
const updatingList = ref(false)
const regionsList = ref<Region[]>([])

// activeRegionLabel 被识别为已声明但未读取，且在模板中未被引用，故移除以通过编译
/*
const activeRegionLabel = computed(() => {
  if (activeRegionCode.value === 'all') return '全域策略视图'
  const match = regions.value.find(r => r.code === activeRegionCode.value)
  return match ? match.name : activeRegionCode.value
})
*/

// 对话框控制
const addOUDialogVisible = ref(false)
const selectedOU = ref('')
const availableOUs = ref<{dn: string, name: string}[]>([])

const simplifyOU = (dn: string) => {
  return dn.split(',').find(item => item.startsWith('OU='))?.replace('OU=', '') || dn
}

const fetchData = async () => {
  loading.value = true
  try {
    // 1. 获取全局设置 (已存的 mapping 和 positions)
    const { data: config } = await axios.get('/api/settings/')
    
    // 初始化 positions
    if (config.POSITIONS) {
      positionList.value = config.POSITIONS.map((p: any) => ({
        ...p,
        default_groups: p.default_groups || []
      }))
    }
    const ouMapping = config.OU_GROUP_MAPPING || {}
    const ouPrefixMapping = config.OU_PREFIX_MAPPING || {}
    defaultPassword.value = config.DEFAULT_USER_PASSWORD || ''

    // 2. 获取 AD 里最新的 Groups 供选择
    const { data: groupsData } = await axios.get('/api/ad/groups')
    groupOptions.value = groupsData.groups || []

    // 3. 获取 AD 里最新的 OUs 用于构建左侧列表
    const { data: ous } = await axios.get('/api/ad/ous')
    ouList.value = ous
    
    // 仅显示已配置的 OU mappings (根据 ouMapping 或 ouPrefixMapping 的 dn 提取)
    const configuredDNs = new Set([
      ...Object.keys(ouMapping),
      ...Object.keys(ouPrefixMapping)
    ])

    const formattedData: Array<{dn: string, name: string, default_groups: string[], prefix: string}> = []
    
    configuredDNs.forEach(dn => {
      const ouInfo = ouList.value.find(item => item.dn === dn)
      formattedData.push({
        dn: dn,
        name: ouInfo ? ouInfo.name : simplifyOU(dn), // 尽量使用拉取的 name，找不到则根据 dn 猜测
        default_groups: ouMapping[dn] || [],
        prefix: ouPrefixMapping[dn] || ''
      })
    })

    // 4. 初始化地区配置
    regions.value = config.REGION_OPTIONS || []
    activeRegionCode.value = config.ACTIVE_REGION_CODE || 'all'
    
    // 初始化字典库管理副本
    regionsList.value = JSON.parse(JSON.stringify(regions.value)).map((r: Region) => ({
      ...r,
      keywordStr: r.keywords.join(', ')
    }))

    ouTableData.value = formattedData

  } catch (err: any) {
    ElMessage.error('获取配置或AD数据失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

const openAddOUDialog = () => {
  // 找出那些还没有被加入表格的 OU
  const addedDNs = ouTableData.value.map(item => item.dn)
  availableOUs.value = ouList.value.filter(ou => !addedDNs.includes(ou.dn))
  selectedOU.value = ''
  addOUDialogVisible.value = true
}

const confirmAddOU = () => {
  const ouInfo = ouList.value.find(o => o.dn === selectedOU.value)
  if (ouInfo) {
    ouTableData.value.push({
      dn: ouInfo.dn,
      name: ouInfo.name,
      default_groups: [],
      prefix: ''
    })
  }
  addOUDialogVisible.value = false
}

const removeOUMapping = (index: number) => {
  ElMessageBox.confirm('确定要删除此 OU 映射配置吗？此操作在保存前不会提交到后端。', '删除提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ouTableData.value.splice(index, 1)
  }).catch(() => {})
}

const addPosition = () => {
  positionList.value.push({ name: '', suffix: '', default_groups: [] })
}

const removePosition = (index: number) => {
  ElMessageBox.confirm('确定要删除此职位配置吗？', '删除提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    positionList.value.splice(index, 1)
  }).catch(() => {})
}

// ---- 地区过滤器方法 ----
const selectRegion = (code: string) => {
  activeRegionCode.value = code
}

const openManage = () => {
  manageVisible.value = true
}

const handleAdd = () => {
  regionsList.value.push({
    name: '新地区',
    code: 'new_region',
    keywords: [],
    keywordStr: ''
  })
}

const removeRegion = (index: number) => {
  ElMessageBox.confirm('确定要从字典库中移除此地区吗？', '删除提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    regionsList.value.splice(index, 1)
  }).catch(() => {})
}

const syncKeywords = (row: Region) => {
  if (row.keywordStr) {
    row.keywords = row.keywordStr.split(/[,，]/).map(s => s.trim()).filter(s => !!s)
  } else {
    row.keywords = []
  }
}

const saveRegionOptions = async () => {
  updatingList.value = true
  try {
    const cleanList = regionsList.value.map(r => ({
      name: r.name,
      code: r.code,
      keywords: r.keywords
    }))
    
    const payload = { region_options: cleanList }
    const { data } = await axios.post('/api/settings/', payload)
    if (data.success) {
      ElMessage.success('地区字典库更新成功')
      manageVisible.value = false
      await fetchData() // 刷新列表
    }
  } catch (err: any) {
    ElMessage.error('更新失败')
  } finally {
    updatingList.value = false
  }
}

const saveTemplates = async () => {
  saving.value = true
  try {
    // 构建待保存的 ou_group_mapping 和 ou_prefix_mapping
    const mappingToSave: Record<string, string[]> = {}
    const prefixToSave: Record<string, string> = {}
    ouTableData.value.forEach(row => {
      // 只有分配了默认组的 OU 我们才存进 config，优化存储大小
      if (row.default_groups && row.default_groups.length > 0) {
        mappingToSave[row.dn] = row.default_groups
      }
      if (row.prefix && row.prefix.trim() !== '') {
        prefixToSave[row.dn] = row.prefix.trim()
      }
    })

    const payload = {
      positions: positionList.value,
      ou_group_mapping: mappingToSave,
      ou_prefix_mapping: prefixToSave,
      default_user_password: defaultPassword.value,
      active_region_code: activeRegionCode.value
    }

    const { data } = await axios.post('/api/settings/', payload)
    if (data.success) {
      ElMessage.success('模板配置保存成功')
    }
  } catch (err: any) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
