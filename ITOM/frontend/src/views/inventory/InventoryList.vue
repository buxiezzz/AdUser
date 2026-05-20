<template>
  <div class="inventory-container">
    <div class="header-section">
      <div class="title-area">
        <h2 class="page-title">资产盘点控制台</h2>
        <p class="page-desc">全流程监控资产清查进度，支持移动端实时同步与报表导出</p>
      </div>
      <el-button type="primary" size="large" @click="showCreateDialog = true">
        + 发起新盘点
      </el-button>
    </div>

    <!-- 盘点任务列表 -->
    <el-card shadow="never" class="list-card">
      <el-table :data="tasks" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已完成' ? 'success' : 'primary'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="盘点进度" min-width="220">
          <template #default="{ row }">
            <div class="progress-col">
              <el-progress :percentage="getPercent(row)" style="flex: 1" />
              <span class="count-hint">{{ row.finished_count }} / {{ row.total_count }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建日期" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="handleExport(row)">导出</el-button>
            <el-popconfirm title="确定删除此盘点任务？此操作不可撤销。" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
            <el-button link type="primary" @click="toggleDetail(row)">
              {{ expandedId === row.id ? '收起' : '明细' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 明细展开（行内卡片，完全避开嵌套 template 的 TS 问题） -->
    <el-card v-if="expandedId" shadow="never" class="detail-card" v-loading="detailLoading">
      <template #header>
        <div class="detail-header">
          <div class="header-left">
            <span>📋 资产核对明细  —  {{ expandedName }}</span>
          </div>
          <div class="header-right">
            <el-input 
              v-model="manualAssetCode" 
              placeholder="输入资产编码或序列号进行核对" 
              size="small" 
              style="width: 250px; margin-right: 10px;"
              @keyup.enter="handleManualCheck"
            >
              <template #append>
                <el-button @click="handleManualCheck">核对入账</el-button>
              </template>
            </el-input>
            <el-button link @click="expandedId = ''">关闭明细</el-button>
          </div>
        </div>
      </template>
      <el-table :data="currentRecords" size="small" border stripe>
        <el-table-column prop="asset_code" label="资产编码" width="180" />
        <el-table-column prop="asset_name" label="设备名称" />
        <el-table-column prop="status" label="盘点状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === '已盘点' ? 'success' : 'info'" effect="dark">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_id" label="核对人" width="120" />
        <el-table-column label="核对时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.audit_time) }}
          </template>
        </el-table-column>
      </el-table>
      <div v-if="currentRecords.length === 0 && !detailLoading" class="empty-detail">
        暂无明细记录
      </div>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="发起新盘点任务" width="500px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="盘点项目名称" required>
          <el-input v-model="createForm.name" placeholder="例如：2024年Q2例行盘点" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="createForm.description" type="textarea" placeholder="备注盘点范围或执行要求" />
        </el-form-item>
        <el-alert
          title="说明：此盘点将默认包含系统中所有在册状态的固定资产。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="submitting">确认发起</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const tasks = ref<any[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const submitting = ref(false)

const expandedId = ref('')
const expandedName = ref('')
const detailLoading = ref(false)
const manualAssetCode = ref('')
const taskRecords = ref<Record<string, any[]>>({})

const createForm = ref({ name: '', description: '' })

// 当前展开任务的记录
const currentRecords = computed(() => {
  if (!expandedId.value) return []
  return taskRecords.value[expandedId.value] || []
})

// 工具函数：格式化时间（接受 any 类型，安全兜底）
function formatTime(val: any): string {
  if (!val) return '-'
  try { return new Date(String(val)).toLocaleString('zh-CN') } catch { return '-' }
}

// 工具函数：计算进度百分比
function getPercent(task: any): number {
  if (!task || !task.total_count) return 0
  return Math.min(100, Math.floor((task.finished_count / task.total_count) * 100))
}

// 展开/关闭明细面板
async function toggleDetail(row: any) {
  if (expandedId.value === row.id) {
    expandedId.value = ''
    return
  }
  expandedId.value = row.id
  expandedName.value = row.name
  if (!taskRecords.value[row.id]) {
    detailLoading.value = true
    try {
      const res = await axios.get(`/api/inventory/tasks/${row.id}/records`)
      taskRecords.value[row.id] = res.data
    } catch {
      ElMessage.error('获取任务明细失败')
    } finally {
      detailLoading.value = false
    }
  }
}

const handleManualCheck = async () => {
  if (!manualAssetCode.value) return ElMessage.warning('请输入资产编码')
  try {
    await axios.post(`/api/inventory/tasks/${expandedId.value}/submit`, { asset_code: manualAssetCode.value })
    ElMessage.success('核对成功')
    manualAssetCode.value = ''
    // 刷新明细和任务列表（更新进度）
    const res = await axios.get(`/api/inventory/tasks/${expandedId.value}/records`)
    taskRecords.value[expandedId.value] = res.data
    fetchTasks()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '核对失败')
  }
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/inventory/tasks')
    tasks.value = res.data || []
  } catch {
    ElMessage.error('获取盘点任务失败')
  } finally {
    loading.value = false
  }
}

const submitCreate = async () => {
  if (!createForm.value.name) return ElMessage.warning('请输入项目名称')
  submitting.value = true
  try {
    await axios.post('/api/inventory/tasks', createForm.value)
    ElMessage.success('盘点任务已发起')
    showCreateDialog.value = false
    createForm.value = { name: '', description: '' }
    fetchTasks()
  } catch {
    ElMessage.error('发起盘点失败')
  } finally {
    submitting.value = false
  }
}

const handleExport = (task: any) => {
  const token = localStorage.getItem('itom_token')
  window.open(`/api/inventory/tasks/${task.id}/export?token=${token}`, '_blank')
}

const handleDelete = async (task: any) => {
  try {
    await axios.delete(`/api/inventory/tasks/${task.id}`)
    ElMessage.success('任务已删除')
    if (expandedId.value === task.id) expandedId.value = ''
    fetchTasks()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchTasks)
</script>

<style scoped>
.inventory-container { padding: 24px; }

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title { margin: 0 0 8px 0; font-size: 24px; font-weight: 600; color: #1a1a1a; }
.page-desc { margin: 0; color: #666; font-size: 14px; }

.list-card { border-radius: 8px; }

.progress-col { display: flex; align-items: center; gap: 12px; }
.count-hint { font-size: 12px; color: #999; white-space: nowrap; }

.detail-card { margin-top: 16px; border-radius: 8px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.header-right { display: flex; align-items: center; }

.empty-detail { padding: 30px; text-align: center; color: #999; font-size: 13px; }
</style>
