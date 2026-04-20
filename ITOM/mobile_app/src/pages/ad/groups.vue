<template>
  <view class="container">
    <scroll-view scroll-y class="list-container">
      <view class="group-card" v-for="(item, index) in groups" :key="index">
        <view class="card-header">
          <text class="name">{{ item.name }}</text>
          <text class="action-btn" @click="viewMembers(item.dn)">查看成员</text>
        </view>
        <view class="card-body">
          <view class="dn-path">{{ item.dn }}</view>
        </view>
      </view>
      
      <view class="empty-state" v-if="!loading && groups.length === 0">暂无安全组数据</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const groups = ref<any[]>([])
const loading = ref(false)

const loadGroups = async () => {
  loading.value = true
  try {
    const res = await request.get('/ad/groups')
    if (res && res.groups) {
      groups.value = res.groups
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const viewMembers = (dn: string) => {
  uni.showToast({ title: '成员管理建议前往 PC 端操作', icon: 'none' })
}

onMounted(() => {
  loadGroups()
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding: 15px;
}

.group-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    
    .name {
      font-size: 16px;
      font-weight: bold;
      color: #333;
    }
    
    .action-btn {
      font-size: 13px;
      color: #007aff;
    }
  }
  
  .card-body {
    .dn-path {
      font-size: 12px;
      color: #888;
      background: #f5f5f5;
      padding: 4px 8px;
      border-radius: 4px;
      word-break: break-all;
    }
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #999;
  font-size: 14px;
}
</style>
