<template>
  <view class="container">
    <view class="search-bar">
      <input class="search-input" v-model="keyword" placeholder="搜索域用户 (如 zhangsan, 张三)" @confirm="onSearch" />
      <view class="search-btn" @click="onSearch">搜索</view>
    </view>
    
    <scroll-view scroll-y class="list-container">
      <view class="user-card" v-for="(item, index) in userList" :key="index">
        <view class="card-left">
          <view class="avatar">{{ getInitials(item.display_name || item.username) }}</view>
        </view>
        <view class="card-content">
          <view class="name-row">
            <text class="name">{{ item.display_name || '未命名' }}</text>
            <text class="username">({{ item.username }})</text>
          </view>
          <view class="ou-row">
            <text class="ou">{{ formatOU(item.dn) }}</text>
          </view>
        </view>
        <view class="card-right">
          <text v-if="item.is_locked" class="status-tag status-locked">已锁定</text>
          <text v-else-if="!item.is_active" class="status-tag status-disabled">已禁用</text>
          <text v-else class="status-tag status-active">正常</text>
        </view>
      </view>
      
      <view class="loading-state" v-if="loading">检索中...</view>
      <view class="empty-state" v-if="!loading && userList.length === 0 && searched">未查找到匹配的域用户</view>
      <view class="empty-state" v-if="!loading && !searched">输入账号或姓名以查找域用户</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import request from '@/utils/request'

const keyword = ref('')
const userList = ref<any[]>([])
const loading = ref(false)
const searched = ref(false)

const onSearch = async () => {
  if (!keyword.value.trim()) {
    uni.showToast({ title: '请输入搜索关键词', icon: 'none' })
    return
  }
  
  loading.value = true
  searched.value = true
  try {
    const res = await request.get('/ad/users', { keyword: keyword.value })
    if (res && res.users) {
      userList.value = res.users
    } else {
      userList.value = []
    }
  } catch (e) {
    console.error(e)
    userList.value = []
  } finally {
    loading.value = false
  }
}

const getInitials = (name: string) => {
  if (!name) return 'U'
  return name.charAt(0).toUpperCase()
}

const formatOU = (dn: string) => {
  if (!dn) return ''
  const parts = dn.split(',')
  if (parts.length > 1) {
    return parts[1].replace('OU=', '') + (parts.length > 2 && parts[2].includes('OU=') ? ` - ${parts[2].replace('OU=', '')}` : '')
  }
  return dn
}
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f9fb;
}

.search-bar {
  display: flex;
  padding: 10px 15px;
  background-color: #fff;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  z-index: 10;
  
  .search-input {
    flex: 1;
    height: 36px;
    background-color: #f5f5f5;
    border-radius: 18px;
    padding: 0 15px;
    font-size: 14px;
  }
  
  .search-btn {
    margin-left: 10px;
    color: #e51923;
    font-size: 15px;
    padding: 5px;
  }
}

.list-container {
  flex: 1;
  padding: 15px;
  
  .user-card {
    background: #fff;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    display: flex;
    align-items: center;
    
    .card-left {
      margin-right: 15px;
      
      .avatar {
        width: 44px;
        height: 44px;
        border-radius: 22px;
        background-color: #e51923;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: bold;
      }
    }
    
    .card-content {
      flex: 1;
      
      .name-row {
        margin-bottom: 4px;
        
        .name {
          font-size: 16px;
          font-weight: bold;
          color: #333;
          margin-right: 6px;
        }
        
        .username {
          font-size: 13px;
          color: #888;
        }
      }
      
      .ou-row {
        .ou {
          font-size: 12px;
          color: #999;
          background: #f5f5f5;
          padding: 2px 6px;
          border-radius: 4px;
        }
      }
    }
    
    .card-right {
      .status-tag {
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 4px;
        
        &.status-active { background: #e6f9ed; color: #00a854; }
        &.status-disabled { background: #f5f5f5; color: #999; }
        &.status-locked { background: #ffe6e6; color: #ff3b30; }
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
