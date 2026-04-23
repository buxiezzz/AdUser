<template>
  <div class="p-2 space-y-6 animate-fade-in">
    <!-- Header Summary -->
    <div class="flex items-end justify-between">
      <div>
        <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">ITOM 实时业务看板</h1>
        <p class="text-gray-500 mt-1">系统全量资产监控与关键审计追踪</p>
      </div>
      <div class="text-right">
        <div class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">最后更新时间</div>
        <div class="text-sm font-mono text-gray-600">{{ lastUpdateTime }}</div>
      </div>
    </div>
    
    <!-- Key Metrics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div v-for="stat in simpleStats" :key="stat.title" 
           class="bg-white rounded-3xl p-6 shadow-sm border border-gray-50 flex items-center hover:shadow-md transition-shadow">
        <div :style="{ backgroundColor: stat.bgColor }" class="p-4 rounded-2xl">
          <el-icon :size="28" :style="{ color: stat.color }"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="ml-5">
          <h2 class="text-gray-500 text-sm font-bold">{{ stat.title }}</h2>
          <p class="text-3xl font-black text-gray-900 mt-1 tracking-tight">{{ stat.value }}</p>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Activity Trend Line Chart -->
      <el-card shadow="never" class="lg:col-span-2 border-0 ring-1 ring-gray-100 rounded-3xl overflow-hidden glass-card">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-bold text-gray-800">系统操作与流动趋势 (7日)</span>
            <el-tag size="small" type="danger" effect="plain" class="rounded-full">实时同步</el-tag>
          </div>
        </template>
        <div class="h-[350px] p-2">
          <VChart :option="trendOption" :loading="statsLoading" />
        </div>
      </el-card>
      
      <!-- Asset Category Pie Chart -->
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-3xl overflow-hidden glass-card">
        <template #header>
          <span class="font-bold text-gray-800">资产构成分布图</span>
        </template>
        <div class="h-[350px] p-2">
          <VChart :option="categoryOption" :loading="statsLoading" />
        </div>
      </el-card>

      <!-- Multi-Location Distribution Pie Chart (Only for Group Admins) -->
      <el-card v-if="isGroupAdmin" shadow="never" class="border-0 ring-1 ring-gray-100 rounded-3xl overflow-hidden glass-card">
        <template #header>
          <span class="font-bold text-gray-800">三地资产占比对比</span>
        </template>
        <div class="h-[350px] p-2">
          <VChart :option="locationOption" :loading="statsLoading" />
        </div>
      </el-card>
    </div>

    <!-- Bottom Row: Logs and Critical Info -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Recent Audit Logs -->
      <el-card shadow="never" class="lg:col-span-2 border-0 ring-1 ring-gray-100 rounded-3xl glass-card">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-bold text-gray-800">最近审计动态</span>
            <el-button link type="danger" @click="router.push('/audit/logs')">查看全部</el-button>
          </div>
        </template>
        <el-table :data="recentLogs" style="width: 100%" v-loading="logsLoading">
          <el-table-column prop="created_at" label="时间" width="120">
            <template #default="{ row }">
              <span class="text-xs font-mono text-gray-400">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="username" label="操作者" width="120">
            <template #default="{ row }">
              <span class="text-sm font-medium text-gray-800">{{ row.username }}</span>
            </template>
          </el-table-column>
          <el-table-column label="动作" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="getActionType(row.action)" effect="light">
                {{ translateAction(row.action) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="target" label="详情描述" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="text-gray-600 text-sm">{{ row.target }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Important Notices or Alerts -->
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-3xl glass-card">
        <template #header>
          <span class="font-bold text-gray-800">高价值/异常资产监控</span>
        </template>
        <div class="space-y-4">
          <div v-for="item in alerts" :key="item.id" class="flex p-3 rounded-xl bg-gray-50 border border-gray-100 items-start space-x-3">
            <div class="mt-1">
              <el-icon :class="item.level === 'warn' ? 'text-amber-500' : 'text-red-500'"><WarningFilled /></el-icon>
            </div>
            <div>
              <div class="text-sm font-bold text-gray-800">{{ item.title }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ item.desc }}</div>
            </div>
          </div>
          <div v-if="alerts.length === 0" class="py-12 text-center text-gray-400">
            <el-icon :size="48"><Checked /></el-icon>
            <p class="mt-2 text-sm">暂无待处理告警</p>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Monitor, CircleCheck, Warning, MagicStick, WarningFilled, Checked } from '@element-plus/icons-vue'
import axios from 'axios'
import VChart from '@/components/VChart.vue'

interface AlertItem {
  id: string
  title: string
  desc: string
  level: string
}

const router = useRouter()
const statsLoading = ref(false)
const logsLoading = ref(false)
const lastUpdateTime = ref('--:--:--')
const recentLogs = ref<any[]>([])
const alerts = ref<AlertItem[]>([])

// Brand Color Scale
const BRAND_RED = '#e51923'
const BRAND_BLACK = '#1a1a1a'

const isGroupAdmin = ref(false)
const simpleStats = reactive([
  { title: '资产总额', value: '0', icon: Monitor, color: BRAND_RED, bgColor: '#fef2f2' },
  { title: '健康运行', value: '0', icon: CircleCheck, color: '#10b981', bgColor: '#ecfdf5' },
  { title: '异常状态', value: '0', icon: Warning, color: '#f59e0b', bgColor: '#fffbeb' },
  { title: '流转次数', value: '0', icon: MagicStick, color: '#8b5cf6', bgColor: '#f5f3ff' },
])

// ECharts Options
const trendOption = ref<any>({
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  xAxis: { type: 'category', data: ['04-17', '04-18', '04-19', '04-20', '04-21', '04-22', '今天'], axisLine: { lineStyle: { color: '#eee' } } },
  yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#eee' } } },
  series: [{
    name: '系统操作',
    type: 'bar',
    barWidth: '30%',
    data: [420, 532, 301, 334, 390, 430, 480],
    itemStyle: {
      color: BRAND_RED,
      borderRadius: [4, 4, 0, 0]
    }
  }, {
    name: '资产流转',
    type: 'line',
    smooth: true,
    data: [120, 182, 191, 234, 290, 330, 310],
    itemStyle: { color: BRAND_BLACK }
  }]
})

const categoryOption = ref<any>({
  tooltip: { trigger: 'item' },
  legend: { show: false },
  series: [{
    name: '资产分类',
    type: 'pie',
    radius: ['40%', '60%'],
    avoidLabelOverlap: true,
    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
    label: {
      show: true,
      position: 'outside',
      formatter: '{b}\n{d}%',
      fontSize: 12,
      fontWeight: 'bold'
    },
    labelLine: { show: true, length: 15, length2: 10 },
    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
    data: [
      { value: 48, name: '移动办公设备' },
      { value: 24, name: '台式工作站' },
      { value: 18, name: '服务器/网络' },
      { value: 10, name: '外设/耗材' }
    ],
    color: [BRAND_RED, BRAND_BLACK, '#4b5563', '#9ca3af']
  }]
})

const locationOption = ref<any>({
  tooltip: { trigger: 'item' },
  legend: { show: false },
  series: [{
    name: '区域分布',
    type: 'pie',
    radius: ['40%', '60%'],
    center: ['50%', '50%'],
    avoidLabelOverlap: true,
    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
    label: {
      show: true,
      position: 'outside',
      formatter: '{b}\n{d}%',
      fontSize: 12,
      fontWeight: 'bold'
    },
    labelLine: { show: true, length: 15, length2: 10 },
    data: [],
    color: ['#e51923', '#1a1a1a', '#4b5563']
  }]
})

const fetchData = async () => {
  statsLoading.value = true
  logsLoading.value = true
  lastUpdateTime.value = new Date().toLocaleTimeString()
  
  try {
    // Dashboard Stats (All-in-one for charts and counts)
    const { data: dashboardRes } = await axios.get('/api/stats/dashboard')
    
    isGroupAdmin.value = dashboardRes.is_group_admin
    
    // Top Stats
    if (dashboardRes && dashboardRes.counts) {
      if (simpleStats[0]) simpleStats[0].value = (dashboardRes.counts.total || 0).toLocaleString()
      if (simpleStats[1]) simpleStats[1].value = ((dashboardRes.counts.total || 0) - (dashboardRes.counts.error || 0)).toLocaleString() // Estimated healthy
      if (simpleStats[2]) simpleStats[2].value = (dashboardRes.counts.error || 0).toLocaleString()
    }
    
    // Category Pie Chart
    if (categoryOption.value.series && categoryOption.value.series[0]) {
      categoryOption.value.series[0].data = dashboardRes.category_dist.length > 0 
        ? dashboardRes.category_dist 
        : [{ value: 0, name: '暂无数据' }]
    }

    // Location Pie Chart
    if (isGroupAdmin.value && locationOption.value.series && locationOption.value.series[0]) {
      locationOption.value.series[0].data = dashboardRes.location_dist
    }

    // Trend Chart
    if (trendOption.value.xAxis && trendOption.value.series) {
      trendOption.value.xAxis.data = dashboardRes.trend.dates
      if (trendOption.value.series[0]) trendOption.value.series[0].data = dashboardRes.trend.values
      if (trendOption.value.series[1]) trendOption.value.series[1].data = dashboardRes.trend.transfers
    }
    
    // Recent Logs
    const { data: logRes } = await axios.get('/api/audit/?limit=8')
    recentLogs.value = logRes.items
    
    // Alerts
    const { data: warnAssets } = await axios.get('/api/assets/?limit=3&status=维修')
    alerts.value = warnAssets.map((a: any) => ({
      id: a.id,
      title: a.asset_code,
      desc: `设备分类: ${a.category?.name || '未知'} | 状态: ${a.status}`,
      level: 'warn'
    }))
    
  } catch (err) {
    console.error('Dashboard data fetch failed', err)
  } finally {
    statsLoading.value = false
    logsLoading.value = false
  }
}

const actionMap: Record<string, string> = {
  'CREATE': '新增记录',
  'UPDATE': '信息变更',
  'DELETE': '删除记录',
  'DELETE_SOFT': '软删除',
  'IMPORT_EXCEL': '批量导入',
  'TRANSFER_APPR': '调拨审批',
  'TRANSFER_SHIP': '确认发货',
  'TRANSFER_RECE': '确认收货',
  'SYNC_AD': 'AD同步',
  'BATCH_UPDATE': '批量修改',
  'LOGIN': '用户登录',
  'EXPORT': '文件导出'
}

const translateAction = (action: string) => {
  return actionMap[action] || action
}

const formatTime = (ts: string) => {
  if (!ts) return ''
  const date = new Date(ts)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

const getActionType = (action: string) => {
  if (action.includes('CREATE') || action.includes('RECE')) return 'success'
  if (action.includes('DELETE')) return 'danger'
  if (action.includes('UPDATE') || action.includes('APPR') || action.includes('SHIP')) return 'warning'
  return 'info'
}

let refreshInterval: any = null
onMounted(() => {
  fetchData()
  refreshInterval = setInterval(fetchData, 60000) // Refresh every minute
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.glass-card {
  background-color: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.5s ease-out forwards;
}
:deep(.el-card__header) {
  border-bottom: 1px solid #f8fafc;
  padding: 18px 24px;
}
:deep(.el-table) {
  --el-table-header-bg-color: #fafafa;
  --el-table-border-color: #f1f5f9;
}
</style>
