<template>
  <view class="container" v-if="detail">
    <view class="header-card">
      <view class="title-row">
        <text class="asset-name">{{ detail.dynamic_attributes?.["设备名称"] || detail.category?.name || '未知设备' }}</text>
        <text :class="['status-badge', statusClass(detail.status)]">{{ detail.status }}</text>
      </view>
      <view class="code-row">
        <text class="label">资产编码：</text>
        <text class="value">{{ detail.asset_code }}</text>
      </view>
    </view>
    
    <view class="section">
      <view class="section-title">基本信息</view>
      <view class="info-list">
        <view class="info-item">
          <text class="label">资产分类</text>
          <text class="value">{{ detail.category?.name || '-' }}</text>
        </view>
        <view class="info-item" v-if="detail.owner">
          <text class="label">当前使用者</text>
          <text class="value">{{ detail.owner.name }} ({{ detail.owner.department }})</text>
        </view>
      </view>
    </view>
    
    <view class="section" v-if="detail.dynamic_attributes && Object.keys(detail.dynamic_attributes).length > 0">
      <view class="section-title">详细属性</view>
      <view class="info-list">
        <view class="info-item" v-for="(v, k) in detail.dynamic_attributes" :key="k">
          <text class="label">{{ k }}</text>
          <text class="value">{{ v || '-' }}</text>
        </view>
      </view>
    </view>
    
    <view class="action-footer">
      <button class="btn primary" @click="handleInventory">快速盘核</button>
      <button class="btn default" @click="changeStatus">流转变更</button>
    </view>
  </view>
  <view class="loading-wrap" v-else>
    <text>加载中...</text>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/utils/request'

const detail = ref<any>(null)
const assetId = ref('')

const loadDetail = async (id: string) => {
  try {
    const res = await request.get(`/assets/${id}`)
    detail.value = res
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

const handleInventory = async () => {
  try {
    uni.showLoading({ title: '核对中...' })
    await request.post(`/assets/${assetId.value}/inventory`)
    uni.hideLoading()
    uni.showToast({ title: '盘点记录已入账', icon: 'success' })
  } catch (e) {
    uni.hideLoading()
  }
}

const changeStatus = () => {
  uni.showActionSheet({
    itemList: ['在用', '在库', '归档', '报废'],
    success: async (res) => {
      const statusList = ['在用', '在库', '归档', '报废']
      const newStatus = statusList[res.tapIndex]
      try {
        uni.showLoading({ title: '更新中...' })
        await request.put(`/assets/${assetId.value}`, { status: newStatus })
        detail.value.status = newStatus
        uni.hideLoading()
        uni.showToast({ title: '状态已更新', icon: 'success' })
      } catch (e) {
        uni.hideLoading()
      }
    }
  })
}

const statusClass = (status: string) => {
  if (status === '在用') return 'status-active'
  if (status === '在库') return 'status-idle'
  if (status === '归档' || status === '报废') return 'status-offline'
  return 'status-default'
}

onLoad((options: any) => {
  if (options && options.id) {
    assetId.value = options.id
    loadDetail(options.id)
  }
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding-bottom: 80px;
}
.loading-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  color: #999;
}

.header-card {
  background: #007aff;
  color: #fff;
  padding: 30px 20px 40px;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  
  .title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    .asset-name {
      font-size: 22px;
      font-weight: bold;
    }
    
    .status-badge {
      font-size: 12px;
      padding: 4px 10px;
      border-radius: 12px;
      background: rgba(255,255,255,0.2);
      
      &.status-active { background: #00a854; }
      &.status-offline { background: #999; }
      &.status-default { background: #ff8c00; }
    }
  }
  
  .code-row {
    font-size: 14px;
    opacity: 0.9;
  }
}

.section {
  background: #fff;
  border-radius: 14px;
  margin: -20px 15px 15px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  position: relative;
  
  & + .section {
    margin-top: 0;
  }
  
  .section-title {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    margin-bottom: 16px;
    border-left: 3px solid #007aff;
    padding-left: 8px;
  }
  
  .info-list {
    .info-item {
      display: flex;
      padding: 10px 0;
      border-bottom: 1px solid #f9f9f9;
      
      &:last-child {
        border-bottom: none;
        padding-bottom: 0;
      }
      
      .label {
        width: 90px;
        color: #888;
        font-size: 14px;
      }
      
      .value {
        flex: 1;
        color: #333;
        font-size: 14px;
        text-align: right;
        word-break: break-all;
      }
    }
  }
}

.action-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  display: flex;
  align-items: center;
  padding: 0 15px;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
  
  .btn {
    flex: 1;
    height: 40px;
    line-height: 40px;
    border-radius: 20px;
    font-size: 15px;
    margin: 0 8px;
    
    &::after { border: none; }
    
    &.primary {
      background: #007aff;
      color: #fff;
    }
    
    &.default {
      background: #f0f0f0;
      color: #333;
    }
  }
}
</style>
