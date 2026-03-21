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
      <button class="btn warning" @click="openPrint">打印标签</button>
      <button class="btn default" @click="changeStatus">流转变更</button>
    </view>

    <!-- 打印预览浮层 -->
    <view class="print-mask" v-if="printVisible" @click="printVisible = false">
      <view class="print-dialog" @click.stop>
        <view class="dialog-header">
          <text class="title">标签预览</text>
          <text class="close" @click="printVisible = false">✕</text>
        </view>
        <view class="dialog-body">
          <view class="print-label-page" id="print-area">
            <table class="print-table">
              <tr>
                <td colspan="2" class="print-title">先惠自动化技术(武汉)有限责任公司</td>
              </tr>
              <tr>
                <td colspan="2" class="print-row">资产编码: {{ detail.asset_code }}</td>
              </tr>
              <tr>
                <td colspan="2" class="print-row">资产名称: {{ detail.category?.name || '未分类' }}</td>
              </tr>
              <tr>
                <td colspan="2" class="print-row">资产型号: {{ detail.dynamic_attributes?.['规格型号'] || '-' }}</td>
              </tr>
              <tr>
                 <td class="print-row">序 列 号 : {{ detail.dynamic_attributes?.['序列号'] || '-' }}</td>
                 <td rowspan="2" class="print-qr-column">
                    <image class="qr-img" :src="getQrUrl(detail)" mode="aspectFit"></image>
                 </td>
              </tr>
              <tr>
                 <td class="print-row">使用日期: {{ detail.created_at ? detail.created_at.split('T')[0] : '-' }}</td>
              </tr>
            </table>
          </view>
        </view>
        <view class="dialog-footer">
          <button class="print-btn" @click="executePrint">呼起系统打印 / 生成 PDF</button>
        </view>
      </view>
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
import { printAssetLabel } from '@/utils/printer'

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

// ---- 标签打印功能 ----
const printVisible = ref(false)

const openPrint = () => {
  printVisible.value = true
}

const getQrUrl = (item: any) => {
  // #ifdef H5
  const origin = `${window.location.protocol}//${window.location.host}`
  const token = item.qr_code_token || ''
  const url = token ? `${origin}/mobile/asset/${token}` : origin
  return `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(url)}`
  // #endif
  
  return `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent('http://10.20.133.62:5173')}`
}

const executePrint = () => {
  printAssetLabel(detail.value)
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
    
    &.warning {
      background: #ff9900;
      color: #fff;
    }
  }
}

/* 打印预览浮层 */
.print-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.print-dialog {
  background: #fff;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  max-width: 360px;
  
  .dialog-header {
    display: flex;
    justify-content: space-between;
    padding: 15px;
    border-bottom: 1px solid #eee;
    
    .title { font-size: 16px; font-weight: bold; color: #333; }
    .close { font-size: 18px; color: #999; }
  }
  
  .dialog-body {
    padding: 20px;
    display: flex;
    justify-content: center;
    background: #f5f5f5;
  }
  
  .dialog-footer {
    padding: 15px;
    border-top: 1px solid #eee;
    
    .print-btn {
      background: #007aff;
      color: #fff;
      border-radius: 20px;
      height: 40px;
      line-height: 40px;
      font-size: 15px;
      &::after { border: none; }
    }
  }
}

/* 标签实体排版 */
.print-label-page {
  width: 70mm;
  height: 50mm;
  background: #fff;
  border: 1.5px solid #000;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: #000;
  box-sizing: border-box;
  padding: 1.5mm;
  overflow: hidden;
  
  .print-table {
    width: 100%;
    height: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    border: 0.8px solid #000;
  }
  
  td {
    border: 0.8px solid #000;
    font-weight: bold;
    font-size: 9px;
    padding: 2px 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .print-title {
    text-align: center;
    font-size: 11px;
    font-weight: 900;
    height: 9mm;
    letter-spacing: -0.5px;
  }
  
  .print-row {
    height: 6.5mm;
  }
  
  .print-qr-column {
    width: 20mm;
    text-align: center;
    vertical-align: middle;
    padding: 1px;
    
    .qr-img {
      width: 18mm;
      height: 18mm;
      display: block;
      margin: 0 auto;
    }
  }
}

/* 打印指令 */
@media print {
  /* 隐藏非打印区域 */
  body *, .container, .print-mask *, .dialog-header, .dialog-footer {
    display: none !important;
  }
  
  .print-mask {
    background: none !important;
    position: static !important;
    display: block !important;
    padding: 0 !important;
  }
  
  .print-dialog {
    box-shadow: none !important;
    border-radius: 0 !important;
    max-width: none !important;
    background: none !important;
    display: block !important;
  }
  
  .dialog-body {
    background: none !important;
    padding: 0 !important;
    display: block !important;
  }
  
  #print-area {
    display: block !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    margin: 0 !important;
    border: 1.5px solid #000 !important;
    page-break-after: always;
  }
  
  @page {
    margin: 0;
    size: 70mm 50mm;
  }
}
</style>
