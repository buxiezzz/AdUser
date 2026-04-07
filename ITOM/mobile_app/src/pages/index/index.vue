<template>
  <view class="container">
    <!-- 顶部 Banner -->
    <view class="header">
      <view class="header-text">
        <text class="hello">ITOM 管理平台</text>
        <text class="subtitle">IT 资产运营管理系统</text>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="quick-grid">
      <view class="quick-item" @click="switchToAsset('')">
        <view class="quick-icon blue">💻</view>
        <text class="quick-label">资产台账</text>
      </view>
      <view class="quick-item" @click="switchToScan">
        <view class="quick-icon orange">📷</view>
        <text class="quick-label">扫描资产</text>
      </view>
      <view class="quick-item" @click="switchToInventory">
        <view class="quick-icon green">☑️</view>
        <text class="quick-label">资产盘点</text>
      </view>
      <view class="quick-item" @click="navTo('/pages/ad/users')">
        <view class="quick-icon purple">🔍</view>
        <text class="quick-label">域用户检索</text>
      </view>
    </view>

    <!-- 统计卡片 -->
    <view class="stat-cards">
      <view class="stat-card blue-card" @click="switchToAsset('在用')">
        <text class="stat-num">{{ statCounts['在用'] || '...' }}</text>
        <text class="stat-label">在用设备</text>
      </view>
      <view class="stat-card green-card" @click="switchToAsset('闲置')">
        <text class="stat-num">{{ statCounts['闲置'] || '...' }}</text>
        <text class="stat-label">闲置设备</text>
      </view>
      <view class="stat-card orange-card" @click="switchToAsset('维修')">
        <text class="stat-num">{{ statCounts['维修'] || '...' }}</text>
        <text class="stat-label">维修中</text>
      </view>
      <view class="stat-card gray-card" @click="switchToAsset('报废')">
        <text class="stat-num">{{ statCounts['报废'] || '...' }}</text>
        <text class="stat-label">已报废</text>
      </view>
    </view>

    <!-- 功能分组 -->
    <view class="section-wrap">
      <view class="section-title">域账号创建</view>
      <view class="section-list">
        <view class="list-item" @click="navTo('/pages/ad/provision')">
          <text class="item-icon">✨</text>
          <text class="item-label">一键创建域账号</text>
          <text class="item-arrow">›</text>
        </view>
        <view class="list-item" @click="navTo('/pages/ad/logs')">
          <text class="item-icon">📝</text>
          <text class="item-label">开通操作日志</text>
          <text class="item-arrow">›</text>
        </view>
        <view class="list-item" @click="navTo('/pages/ad/groups')">
          <text class="item-icon">🛡️</text>
          <text class="item-label">安全组策略</text>
          <text class="item-arrow">›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const statCounts = ref<Record<string, number>>({})

const navTo = (url: string) => {
  const tabPages = [
    '/pages/index/index', 
    '/pages/asset/list', 
    '/pages/scan/index', 
    '/pages/inventory/index', 
    '/pages/settings/index'
  ]
  
  if (tabPages.includes(url)) {
    uni.switchTab({
      url,
      fail: (err) => {
        console.error('switchTab failed', err)
        // 如果 switchTab 失败（可能还没生效为 Tab），尝试 navigateTo
        uni.navigateTo({ url })
      }
    })
  } else {
    uni.navigateTo({ url })
  }
}

const switchToAsset = (status: string) => {
  // 保存状态到本地，供 list 页展示
  if (status) {
    uni.setStorageSync('active_asset_status', status)
  } else {
    uni.removeStorageSync('active_asset_status')
  }
  
  uni.switchTab({ 
    url: '/pages/asset/list',
    success: () => {
       // 触发事件通知 list 页刷新
       uni.$emit('refreshAssetList', { status })
    },
    fail: (err) => {
      console.error('switchTab to asset list failed', err)
      uni.navigateTo({ url: `/pages/asset/list?status=${status}` })
    }
  })
}

const switchToScan = () => {
  navTo('/pages/scan/index')
}

const switchToInventory = () => {
  navTo('/pages/inventory/index')
}

const loadStats = async () => {
  try {
    const statuses = ['在用', '闲置', '维修', '报废']
    const counts: Record<string, number> = {}
    for (const s of statuses) {
      const res = await request.get('/assets/', { status: s, limit: 9999 })
      counts[s] = res?.length || 0
    }
    statCounts.value = counts
  } catch (e) {}
}

onMounted(() => loadStats())
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 20px;
}

.header {
  background: linear-gradient(135deg, #1677ff, #4fa3ff);
  padding: 50px 20px 24px;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  
  .hello {
    display: block;
    font-size: 22px;
    font-weight: 700;
    color: #fff;
  }
  .subtitle {
    display: block;
    font-size: 13px;
    color: rgba(255,255,255,0.75);
    margin-top: 4px;
  }
}

.quick-grid {
  display: flex;
  padding: 16px 16px 8px;
  gap: 12px;
  
  .quick-item {
    flex: 1;
    background: #fff;
    border-radius: 12px;
    padding: 14px 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    
    .quick-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      
      &.blue   { background: #e8f3ff; }
      &.orange { background: #fff4e8; }
      &.green  { background: #e8fff2; }
      &.purple { background: #f0e8ff; }
    }
    
    .quick-label {
      font-size: 12px;
      color: #555;
      text-align: center;
    }
  }
}

.stat-cards {
  display: flex;
  padding: 8px 16px;
  gap: 10px;
  
  .stat-card {
    flex: 1;
    border-radius: 12px;
    padding: 14px 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .stat-num { font-size: 20px; font-weight: 700; color: #fff; }
    .stat-label { font-size: 11px; color: rgba(255,255,255,0.85); margin-top: 4px; }
    
    &.blue-card   { background: #1677ff; }
    &.green-card  { background: #52c41a; }
    &.orange-card { background: #fa8c16; }
    &.gray-card   { background: #8c8c8c; }
  }
}

.section-wrap {
  margin: 12px 16px 0;
  
  .section-title {
    font-size: 13px;
    color: #999;
    margin-bottom: 8px;
    padding-left: 4px;
  }
  
  .section-list {
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    
    .list-item {
      display: flex;
      align-items: center;
      padding: 14px 16px;
      border-bottom: 1px solid #f8f8f8;
      
      &:last-child { border-bottom: none; }
      
      .item-icon  { font-size: 18px; width: 28px; }
      .item-label { flex: 1; font-size: 15px; color: #1a1a1a; }
      .item-arrow { font-size: 18px; color: #ccc; }
    }
  }
}
</style>
