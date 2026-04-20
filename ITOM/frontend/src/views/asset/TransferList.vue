<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">跨归属地资产调拨管控</h1>
      <div class="flex gap-2">
        <el-button @click="fetchTransfers" :icon="Refresh">刷新记录</el-button>
      </div>
    </div>

    <!-- 过滤器 -->
    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <div class="flex flex-wrap gap-4 items-center">
        <el-select v-model="filterStatus" placeholder="单据状态" clearable class="w-40">
          <el-option label="全部状态" value="" />
          <el-option label="待审批" value="待审批" />
          <el-option label="待发货" value="待发货" />
          <el-option label="运输中" value="运输中" />
          <el-option label="已完成" value="已完成" />
          <el-option label="已拒绝" value="已拒绝" />
        </el-select>

        <el-select v-model="filterLocationId" placeholder="相关归属地" clearable class="w-48" v-if="isGroupAdmin">
          <el-option label="全部归属地" :value="null" />
          <el-option v-for="loc in locations" :key="loc.id" :label="loc.name" :value="loc.id" />
        </el-select>

        <span class="text-sm text-gray-400">系统将自动过滤与您当前归属地相关的调拨单据</span>
      </div>
    </el-card>

    <!-- 列表展示 -->
    <el-table :data="transfers" v-loading="loading" border stripe style="width: 100%" class="rounded-xl overflow-hidden">
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="资产信息" min-width="250">
        <template #default="{ row }">
          <div class="flex flex-col">
            <span class="font-mono font-bold text-primary">{{ row.asset?.asset_code || '未知编码' }}</span>
            <span class="text-xs text-gray-500">{{ row.asset?.category?.name || '未知分类' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="调拨路线" width="300">
        <template #default="{ row }">
          <div class="flex items-center space-x-2">
            <el-tag size="small" effect="plain">{{ row.from_location?.name || '未知起点' }}</el-tag>
            <el-icon><Right /></el-icon>
            <el-tag size="small" type="success" effect="plain">{{ row.to_location?.name || '未知终点' }}</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="applicant_name" label="申请人" width="120" />
      <el-table-column prop="created_at" label="申请时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="物流单号" width="180">
        <template #default="{ row }">
          <span v-if="row.tracking_number" class="font-mono text-sm underline decoration-dotted cursor-pointer hover:text-primary" @click="copyTrackingNumber(row.tracking_number)">
            {{ row.tracking_number }}
          </span>
          <span v-else class="text-gray-400">-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <div class="flex gap-2">
            <!-- 审批权：仅限集团超管且状态为待审批 -->
            <template v-if="isGroupAdmin && row.status === '待审批'">
              <el-button size="small" type="primary" @click="handleApprove(row)">通过</el-button>
              <el-button size="small" type="danger" plain @click="handleReject(row)">拒绝</el-button>
            </template>

            <!-- 发货权：调出地管理员或集团超管，且状态为待发货 -->
            <el-button v-if="(isGroupAdmin || row.from_location_id === currentUserLocationId) && row.status === '待发货'" 
                       size="small" type="warning" @click="openShipDialog(row)">填写单号发货</el-button>

            <!-- 签收权：调入地管理员或集团超管，且状态为运输中 -->
            <el-button v-if="(isGroupAdmin || row.to_location_id === currentUserLocationId) && row.status === '运输中'" 
                       size="small" type="success" @click="handleReceive(row)">确认签收</el-button>
            
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 发货弹窗 -->
    <el-dialog v-model="shipDialogVisible" title="填写物流信息并发货" width="400px">
      <el-form :model="shipForm" label-position="top">
        <el-form-item label="物流单号 (顺丰/京东/EMS等)" required>
          <el-input v-model="shipForm.tracking_number" placeholder="请输入运单号" />
        </el-form-item>
        <el-form-item label="发货备注">
          <el-input v-model="shipForm.memo" type="textarea" placeholder="可选填..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitShip">确认向目标地发货</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailsVisible" title="调拨申请单详情" width="550px">
      <div v-if="selectedTransfer" class="space-y-4">
        <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border">
          <div>
            <div class="text-xs text-gray-400">资产编码</div>
            <div class="font-mono font-bold">{{ selectedTransfer.asset?.asset_code }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-400">资产名称</div>
            <div>{{ selectedTransfer.asset?.category?.name }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-400">起始归属地</div>
            <div>{{ selectedTransfer.from_location?.name }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-400">目标归属地</div>
            <div class="text-green-600 font-bold">{{ selectedTransfer.to_location?.name }}</div>
          </div>
        </div>

        <div class="space-y-2">
          <div class="text-xs text-gray-400">流转状态流程</div>
          <el-steps :active="getStepIndex(selectedTransfer.status)" finish-status="success" align-center size="small">
            <el-step title="申请" />
            <el-step title="审批" />
            <el-step title="发货" />
            <el-step title="收货" />
          </el-steps>
        </div>

        <div class="bg-gray-50 p-4 rounded-lg border space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-500">申请人:</span>
            <span>{{ selectedTransfer.applicant_name }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500">审批人:</span>
            <span>{{ selectedTransfer.approver_name || '-' }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500">物流单号:</span>
            <span class="font-mono">{{ selectedTransfer.tracking_number || '-' }}</span>
          </div>
          <div class="flex flex-col text-sm border-t pt-2 mt-2">
            <span class="text-gray-500 mb-1">备注说明:</span>
            <div class="text-gray-700 italic bg-white p-2 rounded border-l-4 border-blue-400">{{ selectedTransfer.memo || '无' }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Refresh, Right } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const transfers = ref<any[]>([])
const locations = ref<any[]>([])
const isGroupAdmin = ref(false)
const currentUserLocationId = ref<number | null>(null)

const filterStatus = ref('')
const filterLocationId = ref<number | null>(null)

const fetchTransfers = async () => {
  loading.value = true
  try {
    const params: any = {
      limit: 100
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterLocationId.value) params.location_id = filterLocationId.value

    const { data } = await axios.get('/api/transfers/', { params })
    transfers.value = data
  } catch (e) {
    ElMessage.error('无法加载调拨记录')
  } finally {
    loading.value = false
  }
}

const fetchMetadata = async () => {
  try {
    const [locRes, userRes] = await Promise.all([
      axios.get('/api/locations/'),
      axios.get('/api/auth/me')
    ])
    locations.value = locRes.data
    isGroupAdmin.value = userRes.data.is_group_admin
    currentUserLocationId.value = userRes.data.location_id
  } catch (e) {}
}

onMounted(() => {
  fetchMetadata()
  fetchTransfers()
})

watch([filterStatus, filterLocationId], () => {
  fetchTransfers()
})

const getStatusType = (status: string) => {
  const map: any = {
    '待审批': 'info',
    '待发货': 'warning',
    '运输中': 'primary',
    '已完成': 'success',
    '已拒绝': 'danger'
  }
  return map[status] || ''
}

const getStepIndex = (status: string) => {
  const map: any = {
    '待审批': 0,
    '待发货': 1,
    '运输中': 2,
    '已完成': 4,
    '已拒绝': 0
  }
  return map[status] || 0
}

// 审批操作
const handleApprove = (row: any) => {
  ElMessageBox.confirm('确定批准该资产跨地区调拨申请吗？', '审批确认', {
    type: 'success'
  }).then(async () => {
    await axios.put(`/api/transfers/${row.id}`, { status: '待发货' })
    ElMessage.success('已审批通过，等待发货')
    fetchTransfers()
  })
}

const handleReject = (row: any) => {
  ElMessageBox.prompt('请输入拒绝原因', '审批拒绝', {
    inputPlaceholder: '由于...'
  }).then(async ({ value }) => {
    await axios.put(`/api/transfers/${row.id}`, { status: '已拒绝', memo: value })
    ElMessage.info('已拒绝调拨申请')
    fetchTransfers()
  })
}

// 发货弹窗
const shipDialogVisible = ref(false)
const submitting = ref(false)
const currentSelectedRow = ref<any>(null)
const shipForm = ref({
  tracking_number: '',
  memo: ''
})

const openShipDialog = (row: any) => {
  currentSelectedRow.value = row
  shipForm.value = { tracking_number: '', memo: '' }
  shipDialogVisible.value = true
}

const submitShip = async () => {
  if (!shipForm.value.tracking_number) return ElMessage.warning('请填写物流单号')
  submitting.value = true
  try {
    await axios.put(`/api/transfers/${currentSelectedRow.value.id}`, {
      status: '运输中',
      tracking_number: shipForm.value.tracking_number,
      memo: shipForm.value.memo
    })
    ElMessage.success('发货成功，资产状态已更新为调拨中')
    shipDialogVisible.value = false
    fetchTransfers()
  } finally {
    submitting.value = false
  }
}

// 签收
const handleReceive = (row: any) => {
  ElMessageBox.confirm('资产已安全送达并核对无误了吗？签收后资产归属地将自动变更。', '确认签收', {
    confirmButtonText: '确认签收',
    type: 'success'
  }).then(async () => {
    await axios.put(`/api/transfers/${row.id}`, { status: '已完成' })
    ElMessage.success('签收完成，资产已入库新归属地')
    fetchTransfers()
  })
}

const detailsVisible = ref(false)
const selectedTransfer = ref<any>(null)
const viewDetails = (row: any) => {
  selectedTransfer.value = row
  detailsVisible.value = true
}

const copyTrackingNumber = (text: string) => {
  navigator.clipboard.writeText(text)
  ElMessage.success('物流单号已复制到剪贴板')
}
</script>
