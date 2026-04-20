<template>
  <view class="page-wrap">
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <text class="title">盘点任务大厅</text>
      <text class="nav-action" @click="goToCreate">发起盘点</text>
    </view>

    <scroll-view scroll-y class="list-container" @scrolltolower="loadTasks">
      <view class="task-card" v-for="task in tasks" :key="task.id" @click="goToTask(task)">
        <view class="card-header">
          <view class="left">
            <text class="task-name">{{ task.name }}</text>
            <text :class="['status-tag', task.status === '已完成' ? 'done' : 'doing']">{{ task.status }}</text>
          </view>
          <text class="delete-btn" @click.stop="confirmDelete(task)">🗑️</text>
        </view>
        <text class="task-desc">{{ task.description || '无任务描述' }}</text>
        
        <view class="progress-wrap">
          <view class="progress-info">
            <text class="progress-text">完成进度：{{ task.finished_count }} / {{ task.total_count }}</text>
            <text class="progress-percent">{{ calculatePercent(task) }}%</text>
          </view>
          <view class="progress-bar-bg">
            <view class="progress-bar-inner" :style="{ width: calculatePercent(task) + '%' }"></view>
          </view>
        </view>

        <view class="card-footer">
          <text class="time">创建于：{{ formatDate(task.created_at) }}</text>
          <text class="action">进入核对 ›</text>
        </view>
      </view>

      <view class="empty-tip" v-if="tasks.length === 0 && !loading">
        <text class="icon">📁</text>
        <text class="text">暂无进行中的盘点任务</text>
      </view>
    </scroll-view>
    <CustomTabBar :activeIndex="3" />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import request from '@/utils/request'
import CustomTabBar from '@/components/CustomTabBar.vue'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 20)
const tasks = ref<any[]>([])
const loading = ref(false)

const loadTasks = async () => {
  if (loading.value) return
  loading.value = true
  try {
    // 默认展示最近 20 条盘点任务
    const res = await request.get('/inventory/tasks', { limit: 20 })
    tasks.value = res || []
  } catch (e) {
  } finally {
    loading.value = false
  }
}

const calculatePercent = (task: any) => {
  if (!task.total_count) return 0
  return Math.floor((task.finished_count / task.total_count) * 100)
}

const formatDate = (date: string) => {
  return date ? date.split('T')[0] : '-'
}

const goToTask = (task: any) => {
  uni.navigateTo({
    url: `/pages/inventory/execute?id=${task.id}&name=${encodeURIComponent(task.name)}`
  })
}

const goToCreate = () => {
  uni.navigateTo({
    url: '/pages/inventory/create'
  })
}

const confirmDelete = (task: any) => {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除盘点任务“${task.name}”吗？关联的所有记录也将被清除。`,
    confirmColor: '#ff4d4f',
    success: async (res) => {
      if (res.confirm) {
        try {
          await request.delete(`/inventory/tasks/${task.id}`)
          uni.showToast({ title: '删除成功', icon: 'success' })
          loadTasks()
        } catch (e: any) {
          uni.showToast({ title: e?.data?.detail || '删除失败', icon: 'none' })
        }
      }
    }
  })
}

onShow(() => {
  uni.hideTabBar()
  loadTasks()
})
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #f7f9fc;
}
.header {
  background: #fff;
  padding-bottom: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-bottom: 1px solid #efefef;
  position: relative;
  .title { font-size: 17px; font-weight: 600; color: #333; }
  .nav-action {
    position: absolute;
    right: 15px;
    font-size: 14px;
    color: #1677ff;
    font-weight: 500;
  }
}

.list-container {
  padding: 15px;
  box-sizing: border-box;
}

.task-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    
    .left {
      display: flex;
      flex-direction: column;
      gap: 4px;
      .task-name { font-size: 16px; font-weight: bold; color: #1a1a1a; }
      .status-tag {
        align-self: flex-start;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
        &.doing { background: #e6f7ff; color: #1890ff; }
        &.done { background: #f6ffed; color: #52c41a; }
      }
    }
    
    .delete-btn {
      font-size: 18px;
      padding: 4px;
      color: #ff4d4f;
      &:active { opacity: 0.6; }
    }
  }
  
  .task-desc { font-size: 13px; color: #888; margin-bottom: 16px; }
  
  .progress-wrap {
    margin-bottom: 16px;
    .progress-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 12px;
      .progress-text { color: #666; }
      .progress-percent { color: #1677ff; font-weight: bold; }
    }
    .progress-bar-bg {
      height: 6px;
      background: #f0f0f0;
      border-radius: 3px;
      overflow: hidden;
      .progress-bar-inner {
        height: 100%;
        background: linear-gradient(90deg, #1677ff, #4fa3ff);
        transition: width 0.3s ease;
      }
    }
  }
  
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #f9f9f9;
    padding-top: 12px;
    .time { font-size: 11px; color: #ccc; }
    .action { font-size: 13px; color: #1677ff; font-weight: 500; }
  }
}

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 100px;
  .icon { font-size: 60px; margin-bottom: 16px; }
  .text { color: #999; font-size: 14px; }
}
</style>
