<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800 tracking-tight">归属地管理</h1>
        <p class="text-sm text-gray-500 mt-1">管理集团下的子公司/分部，每个归属地独立管理各自资产</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog" v-if="isGroupAdmin">
        新增归属地
      </el-button>
    </div>

    <!-- 归属地卡片网格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <el-card
        v-for="loc in locations"
        :key="loc.id"
        shadow="hover"
        class="border-0 ring-1 ring-gray-100 rounded-xl overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1"
        :class="{ 'opacity-50': !loc.is_active }"
      >
        <!-- 顶部渐变条 -->
        <div class="h-2 w-full -mt-5 -mx-5 mb-4" :style="{ background: getGradient(loc.code), width: 'calc(100% + 40px)' }"></div>
        
        <div class="flex items-start justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md" :style="{ background: getGradient(loc.code) }">
              {{ loc.code }}
            </div>
            <div>
              <h3 class="text-lg font-bold text-gray-800">{{ loc.name }}</h3>
              <el-tag v-if="loc.is_active" type="success" size="small" effect="plain" class="mt-1">运营中</el-tag>
              <el-tag v-else type="info" size="small" effect="plain" class="mt-1">已停用</el-tag>
            </div>
          </div>
          <el-dropdown trigger="click" v-if="isGroupAdmin" @command="(cmd: string) => handleCommand(cmd, loc)">
            <el-button text :icon="MoreFilled" circle />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit" :icon="Edit">编辑</el-dropdown-item>
                <el-dropdown-item command="delete" :icon="Delete" divided class="text-red-500">停用</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="mt-4 space-y-2 text-sm text-gray-600">
          <div class="flex items-center" v-if="loc.address">
            <el-icon class="mr-2 text-gray-400"><Location /></el-icon>
            <span>{{ loc.address }}</span>
          </div>
          <div class="flex items-center" v-if="loc.contact_person">
            <el-icon class="mr-2 text-gray-400"><User /></el-icon>
            <span>{{ loc.contact_person }}</span>
          </div>
          <div class="flex items-center" v-if="loc.contact_phone">
            <el-icon class="mr-2 text-gray-400"><Phone /></el-icon>
            <span>{{ loc.contact_phone }}</span>
          </div>
        </div>

        <!-- 资产统计 -->
        <div class="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
          <div class="text-center flex-1">
            <div class="text-xl font-bold text-primary">{{ getAssetCount(loc.id) }}</div>
            <div class="text-xs text-gray-400 mt-1">资产总数</div>
          </div>
          <div class="w-px h-8 bg-gray-100"></div>
          <div class="text-center flex-1">
            <div class="text-xl font-bold text-emerald-500">{{ getInUseCount(loc.id) }}</div>
            <div class="text-xs text-gray-400 mt-1">在用</div>
          </div>
          <div class="w-px h-8 bg-gray-100"></div>
          <div class="text-center flex-1">
            <div class="text-xl font-bold text-amber-500">{{ getIdleCount(loc.id) }}</div>
            <div class="text-xs text-gray-400 mt-1">闲置</div>
          </div>
        </div>
      </el-card>

      <!-- 无归属地的资产统计卡片 -->
      <el-card 
        v-if="unassignedCount > 0"
        shadow="hover"
        class="border-0 ring-1 ring-amber-200 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50"
      >
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center text-amber-600">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <div>
            <h3 class="text-lg font-bold text-gray-800">未分配归属地</h3>
            <p class="text-sm text-amber-600 mt-1">共 {{ unassignedCount }} 项资产待分配</p>
          </div>
        </div>
        <div class="mt-4">
          <el-button type="warning" plain size="small" @click="goToAssetList" v-if="isGroupAdmin">
            前往资产台账分配
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingLocation ? '编辑归属地' : '新增归属地'"
      width="500px"
      class="rounded-2xl"
    >
      <el-form :model="formData" label-position="top" ref="formRef" :rules="formRules">
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="归属地编码" prop="code">
            <el-input v-model="formData.code" placeholder="如: SH, WH, CS" :disabled="!!editingLocation" />
          </el-form-item>
          <el-form-item label="归属地名称" prop="name">
            <el-input v-model="formData.name" placeholder="如: 上海总部" />
          </el-form-item>
        </div>
        <el-form-item label="详细地址">
          <el-input v-model="formData.address" placeholder="请输入详细地址" />
        </el-form-item>
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="负责人">
            <el-input v-model="formData.contact_person" placeholder="请输入负责人姓名" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="formData.contact_phone" placeholder="请输入联系电话" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">
            {{ editingLocation ? '保存修改' : '确认创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Edit, Delete, MoreFilled, Location, User, Phone, Warning } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()

interface LocationItem {
  id: number
  code: string
  name: string
  address?: string
  contact_person?: string
  contact_phone?: string
  is_active: boolean
}

const locations = ref<LocationItem[]>([])
const isGroupAdmin = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editingLocation = ref<LocationItem | null>(null)
const formRef = ref<FormInstance>()

// 资产统计数据
const assetStats = ref<Record<number, { total: number; in_use: number; idle: number }>>({})
const unassignedCount = ref(0)

const formData = reactive({
  code: '',
  name: '',
  address: '',
  contact_person: '',
  contact_phone: ''
})

const formRules = reactive<FormRules>({
  code: [{ required: true, message: '请输入归属地编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入归属地名称', trigger: 'blur' }]
})

// 渐变色方案
const gradientMap: Record<string, string> = {
  SH: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  WH: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  CS: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
}
const defaultGradients = [
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)'
]

const getGradient = (code: string) => {
  if (gradientMap[code]) return gradientMap[code]
  const idx = code.charCodeAt(0) % defaultGradients.length
  return defaultGradients[idx]
}

const getAssetCount = (locationId: number) => assetStats.value[locationId]?.total ?? 0
const getInUseCount = (locationId: number) => assetStats.value[locationId]?.in_use ?? 0
const getIdleCount = (locationId: number) => assetStats.value[locationId]?.idle ?? 0

const fetchLocations = async () => {
  try {
    const { data } = await axios.get('/api/locations/', { params: { include_inactive: isGroupAdmin.value } })
    locations.value = data
  } catch (err) {
    ElMessage.error('获取归属地列表失败')
  }
}

const fetchAssetStats = async () => {
  try {
    // 获取所有资产并统计
    const { data: assets } = await axios.get('/api/assets/', { params: { limit: 99999 } })
    const stats: Record<number, { total: number; in_use: number; idle: number }> = {}
    let unassigned = 0

    for (const asset of assets) {
      if (!asset.location_id) {
        unassigned++
        continue
      }
      if (!stats[asset.location_id]) {
        stats[asset.location_id] = { total: 0, in_use: 0, idle: 0 }
      }
      const s = stats[asset.location_id]
      if (s) {
        s.total++
        if (asset.status === '在用') s.in_use++
        if (asset.status === '闲置') s.idle++
      }
    }

    assetStats.value = stats
    unassignedCount.value = unassigned
  } catch (err) {
    console.warn('获取资产统计失败', err)
  }
}

const fetchUserInfo = async () => {
  try {
    const { data } = await axios.get('/api/auth/me')
    isGroupAdmin.value = data.is_group_admin
  } catch (err) {
    console.warn('获取用户信息失败')
  }
}

const openCreateDialog = () => {
  editingLocation.value = null
  formData.code = ''
  formData.name = ''
  formData.address = ''
  formData.contact_person = ''
  formData.contact_phone = ''
  dialogVisible.value = true
}

const handleCommand = (cmd: string, loc: LocationItem) => {
  if (cmd === 'edit') {
    editingLocation.value = loc
    formData.code = loc.code
    formData.name = loc.name
    formData.address = loc.address || ''
    formData.contact_person = loc.contact_person || ''
    formData.contact_phone = loc.contact_phone || ''
    dialogVisible.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定要停用归属地「${loc.name}」吗？停用后该归属地将不再出现在选项中。`, '确认停用', {
      confirmButtonText: '确认停用',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      try {
        await axios.delete(`/api/locations/${loc.id}`)
        ElMessage.success('归属地已停用')
        fetchLocations()
      } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '停用失败')
      }
    }).catch(() => {})
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editingLocation.value) {
        await axios.put(`/api/locations/${editingLocation.value.id}`, formData)
        ElMessage.success('归属地信息已更新')
      } else {
        await axios.post('/api/locations/', formData)
        ElMessage.success('归属地创建成功')
      }
      dialogVisible.value = false
      fetchLocations()
      fetchAssetStats()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    } finally {
      saving.value = false
    }
  })
}

const goToAssetList = () => {
  router.push('/assets/list')
}

onMounted(async () => {
  await fetchUserInfo()
  await fetchLocations()
  await fetchAssetStats()
})
</script>
