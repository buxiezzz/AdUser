<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">权限模板配置</h1>
      <el-button type="primary" :loading="saving" @click="saveTemplates">
        <el-icon class="mr-1"><Check /></el-icon>
        保存所有模板配置
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Check, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
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
  ouTableData.value.splice(index, 1)
}

const addPosition = () => {
  positionList.value.push({ name: '', suffix: '', default_groups: [] })
}

const removePosition = (index: number) => {
  positionList.value.splice(index, 1)
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
      ou_prefix_mapping: prefixToSave
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
