<template>
  <div class="p-6 space-y-6">
    <!-- 顶部状态卡片 -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ pageTitle }}</h1>
        <p class="text-sm text-gray-500 mt-1">记录系统核心业务数据的变更轨迹，确保运维行为合规可审计。</p>
      </div>
      <el-button @click="fetchLogs" :icon="Refresh" circle shadow="always" />
    </div>

    <!-- 过滤器与报表概览 (可选扩充) -->
    <el-card shadow="never" class="border-gray-100 rounded-2xl">
      <div class="flex items-center space-x-4">
        <el-input
          v-model="queryParams.target"
          placeholder="搜索目标标识 (如资产号、用户名)"
          class="max-w-xs"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          unlink-panels
          clearable
          @change="handleDateChange"
        />
        
        <el-button type="primary" :icon="Search" @click="handleSearch">筛选</el-button>
      </div>
    </el-card>

    <!-- 日志列表主体 -->
    <el-card shadow="never" class="border-gray-100 rounded-3xl overflow-hidden mt-4">
      <el-table 
        :data="logs" 
        v-loading="loading" 
        stripe 
        style="width: 100%"
        :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: 'bold' }"
      >
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-600 font-mono text-xs">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="操作账号" width="150" />
        
        <el-table-column prop="action" label="动作类型" width="160">
          <template #default="{ row }">
            <el-tag :type="getActionTag(row.action)" effect="plain" class="rounded-lg">
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="target" label="目标标识" width="200">
          <template #default="{ row }">
            <span class="font-bold text-primary-dark">{{ row.target }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="details" label="变更详情">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.details"
              effect="dark"
              placement="top"
              :content="row.details"
            >
              <span class="text-xs text-gray-400 cursor-help truncate block max-w-xs">
                {{ row.details }}
              </span>
            </el-tooltip>
            <span v-else class="text-gray-300">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
      </el-table>

      <div class="mt-6 flex justify-end">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
          class="pb-4"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { Refresh, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()

// 根据路由参数确定模块 (asset 或 ad)
const currentModule = computed(() => route.meta.module as string || 'asset')
const pageTitle = computed(() => currentModule.value === 'asset' ? '资产操作日志' : '域账号操作日志')

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const dateRange = ref([])

const queryParams = reactive({
  page: 1,
  limit: 20,
  target: '',
  module: currentModule.value
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/audit/', {
      params: {
        module: currentModule.value,
        skip: (queryParams.page - 1) * queryParams.limit,
        limit: queryParams.limit,
        target: queryParams.target
      }
    })
    logs.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('Failed to fetch logs', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchLogs()
}

const handleDateChange = (val: any) => {
  // 暂时仅在前端简单记录，如需后端过滤需扩充 API
  console.log('Date changed', val)
}

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const getActionTag = (action: string) => {
  if (action.includes('CREATE') || action === 'PROVISION') return 'success'
  if (action.includes('DELETE')) return 'danger'
  if (action.includes('UPDATE') || action.includes('RESET')) return 'warning'
  return 'info'
}

// 监听路由变化，切换模块时重新加载
watch(() => currentModule.value, (newVal) => {
  queryParams.module = newVal
  queryParams.page = 1
  fetchLogs()
})

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
:deep(.el-table__row) {
  transition: all 0.3s;
}
:deep(.el-table__row:hover) {
  background-color: #f1f5f9 !important;
}
</style>
