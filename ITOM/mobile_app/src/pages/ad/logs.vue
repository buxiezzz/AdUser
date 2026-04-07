<template>
  <view class="container">
    <view class="list-container">
      <view class="log-card" v-for="(log, index) in logs" :key="index">
        <view class="log-header">
          <text class="log-type" :class="getActionClass(log.action)">{{ log.action }}</text>
          <text class="log-time">{{ formatTime(log.created_at) }}</text>
        </view>
        <view class="log-content">
          <view class="log-row">
            <text class="label">运维账号:</text>
            <text class="value">{{ log.username }}</text>
          </view>
          <view class="log-row">
            <text class="label">操作目标:</text>
            <text class="value target">{{ log.target }}</text>
          </view>
          <view class="log-row" v-if="log.details">
            <text class="label">变更详情:</text>
            <text class="value detail-text">{{ log.details }}</text>
          </view>
        </view>
      </view>
      
      <view class="loading-state" v-if="loading">加载中...</view>
      <view class="empty-state" v-if="!loading && logs.length === 0">暂无相关操作日志</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const logs = ref<any[]>([])
const loading = ref(false)

const fetchLogs = async () => {
  loading.value = true
  try {
    // 移动端主要关注 ad 模块日志
    const res = await request.get('/audit/', { module: 'ad', limit: 50 })
    if (res && res.items) {
      logs.value = res.items
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatTime = (time: string) => {
  if (!time) return ''
  const d = new Date(time)
  const pad = (n: number) => n < 10 ? '0' + n : n
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const getActionClass = (action: string) => {
  if (action.includes('PROVISION') || action.includes('CREATE')) return 'type-create'
  if (action.includes('DELETE')) return 'type-delete'
  return 'type-update'
}

onMounted(() => {
  fetchLogs()
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding: 15px;
}

.log-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 10px rgba(0,0,0,0.03);
  
  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    border-bottom: 1px solid #f1f1f1;
    padding-bottom: 8px;
    
    .log-type {
      font-size: 13px;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 700;
      
      &.type-create { background: #e6f9ed; color: #00a854; }
      &.type-delete { background: #ffe6e6; color: #ff3b30; }
      &.type-update { background: #fff7e6; color: #fa8c16; }
    }
    
    .log-time {
      font-size: 12px;
      color: #999;
    }
  }
  
  .log-content {
    .log-row {
      display: flex;
      margin-bottom: 6px;
      font-size: 14px;
      
      .label {
        color: #999;
        width: 70px;
      }
      
      .value {
        color: #333;
        flex: 1;
        
        &.target {
          font-weight: bold;
          color: #007aff;
        }
        
        &.detail-text {
          font-size: 12px;
          color: #888;
          word-break: break-all;
        }
      }
    }
  }
}

.loading-state, .empty-state {
  text-align: center;
  padding: 40px 0;
  color: #999;
  font-size: 14px;
}
</style>
