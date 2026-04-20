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
    
    <!-- Tab 切换 -->
    <view class="tab-strip">
      <view class="tab-item" :class="{ active: currentTab === 'details' }" @tap="switchTab('details')">
        资产详情
      </view>
      <view class="tab-item" :class="{ active: currentTab === 'logs' }" @tap="switchTab('logs')">
        操作记录
      </view>
    </view>

    <!-- 资产详情 Tab -->
    <view v-if="currentTab === 'details'">
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
    </view>

    <!-- 操作记录 Tab -->
    <view v-if="currentTab === 'logs'" class="logs-container">
      <view class="log-item" v-for="log in logs" :key="log.id">
        <view class="log-timeline">
          <view class="log-dot"></view>
          <view class="log-line"></view>
        </view>
        <view class="log-content">
          <view class="log-header">
            <text class="log-action">{{ log.action }}</text>
            <text class="log-date">{{ formatDate(log.created_at) }}</text>
          </view>
          <view class="log-detail" v-if="log.previous_owner_name || log.new_owner_name">
            流转：{{ log.previous_owner_name || '无' }} ➔ {{ log.new_owner_name || '无' }}
          </view>
          <view class="log-detail">
            操作人：{{ log.operator_name || '系统' }}
          </view>
          <view class="log-memo" v-if="log.memo">
            备注：{{ log.memo }}
          </view>
        </view>
      </view>
      <view class="empty-logs" v-if="logs.length === 0">
        <text>暂无操作记录</text>
      </view>
    </view>
    
    <view class="action-footer">
      <button class="btn warning" @click="openPrint">打印标签</button>
      <button class="btn primary" @click="openUnifiedChange">信息变更</button>
      <button class="btn info" @click="navToTransferApply">调拨申请</button>
    </view>

    <!-- 综合变更浮层 -->
    <view class="print-mask" v-if="changeVisible" @click="closeChange">
      <view class="print-dialog" @click.stop style="max-height: 70vh;">
        <view class="dialog-header">
          <text class="title">资产信息变更</text>
          <text class="close" @click="closeChange">✕</text>
        </view>
        <scroll-view scroll-y class="change-body-scroll">
          <view class="change-body">
            <view class="change-item">
               <text class="c-label">当前状态</text>
               <picker mode="selector" :range="statusList" :value="statusList.indexOf(pendingStatus)" @change="onPendingStatusChange">
                  <view class="c-val">
                     {{ pendingStatus }}
                     <text class="c-arrow">›</text>
                  </view>
               </picker>
            </view>
            
            <view class="change-item" @click="navToSelect">
               <text class="c-label">使用人 / 管理人</text>
               <view class="c-val" :class="{ placeholder: !pendingOwner }">
                  {{ pendingOwner ? pendingOwner.name : '点此指派人员' }}
                  <text class="c-arrow">›</text>
               </view>
            </view>
            
            <view class="tip-text" v-if="pendingStatus === '闲置' && pendingOwner">
               注意：设为闲置将自动清空当前使用人
            </view>
            
            <view class="attr-edit-section">
               <view class="section-divider">详细属性编辑</view>
               <view class="change-item" v-for="(v, k) in pendingAttributes" :key="k">
                  <text class="c-label">{{ k }}</text>
                  <input class="c-input" v-model="pendingAttributes[k]" placeholder="请输入内容" />
               </view>
            </view>
          </view>
        </scroll-view>
        <view class="dialog-footer">
          <button class="submit-btn" :loading="saving" @click="submitChange">确认保存变更</button>
        </view>
      </view>
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
  <view class="loading-wrap" v-else-if="errMsg">
    <text class="err-icon">⚠️</text>
    <text class="err-text">{{ errMsg }}</text>
    <view class="retry-btn" @tap="loadDetail(assetId)">
      <text class="retry-text">重新加载</text>
    </view>
  </view>
  <view class="loading-wrap" v-else>
    <text>加载中...</text>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/utils/request'
import { printAssetLabel } from '@/utils/printer'

const detail = ref<any>(null)
const assetId = ref('')
const errMsg = ref('')
const currentTab = ref('details')
const logs = ref<any[]>([])

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 16)
}

const switchTab = (tab: string) => {
  currentTab.value = tab
  if (tab === 'logs' && logs.value.length === 0) {
    loadLogs(assetId.value)
  }
}

const loadLogs = async (id: string) => {
  try {
    const res = await request.get(`/assets/${id}/logs`)
    logs.value = res || []
  } catch (e) {
    console.error('加载日志失败', e)
  }
}

const loadDetail = async (id: string) => {
  errMsg.value = ''
  try {
    console.log('[detail] 开始加载资产, id:', id)
    const res = await request.get(`/assets/${id}`)
    console.log('[detail] 加载成功:', JSON.stringify(res))
    detail.value = res
  } catch (e: any) {
    // request.ts 已经 showToast 了具体错误, 这里记录额外信息
    const msg = e?.data?.detail || e?.errMsg || '网络请求失败，请检查服务器连接或重新登录'
    console.error('[detail] 加载失败:', JSON.stringify(e))
    errMsg.value = msg
    // 不再重复 showToast，由 request.ts 处理
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

const statusClass = (status: string) => {
  if (status === '在用') return 'status-active'
  if (status === '闲置') return 'status-idle'
  if (status === '维修') return 'status-repair'
  return 'status-offline' // 报废、下账
}

const printVisible = ref(false)
const changeVisible = ref(false)
const saving = ref(false)
const statusList = ['在用', '闲置', '维修', '报废', '下账']
const pendingStatus = ref('')
const pendingOwner = ref<any>(null)

const openUnifiedChange = () => {
  pendingStatus.value = detail.value.status
  pendingOwner.value = detail.value.owner
  // 深拷贝动态属性用于编辑
  pendingAttributes.value = JSON.parse(JSON.stringify(detail.value.dynamic_attributes || {}))
  changeVisible.value = true
}

const closeChange = () => {
  if (saving.value) return
  changeVisible.value = false
}

const onPendingStatusChange = (e: any) => {
  pendingStatus.value = statusList[e.detail.value]
}

const navToSelect = () => {
  if (pendingStatus.value === '报废' || pendingStatus.value === '下账') {
    uni.showToast({ title: '已下账或报废资产无法变更人员', icon: 'none' })
    return
  }
  uni.navigateTo({ url: '/pages/employee/select' })
}

const pendingAttributes = ref<any>({})

const submitChange = async () => {
  if (saving.value) return
  
  // 业务校验：如果设为闲置，强制清空人员
  let finalOwnerId = pendingOwner.value?.id || null
  if (pendingStatus.value === '闲置' || pendingStatus.value === '报废' || pendingStatus.value === '下账') {
    finalOwnerId = null
  }

  try {
    saving.value = true
    uni.showLoading({ title: '同步到服务器...' })

    // 构造全量更新对象，确保原子化操作
    const updatePayload: any = {
      status: pendingStatus.value,
      owner_id: finalOwnerId,
      dynamic_attributes: pendingAttributes.value
    }
    
    // 发起单一 PUT 请求，彻底解决同步不一致问题
    const updatedAsset = await request.put(`/assets/${assetId.value}`, updatePayload)
    
    if (updatedAsset) {
      // 成功后全量同步本地状态
      detail.value = updatedAsset
      uni.showToast({ title: '云端同步成功', icon: 'success' })
      loadLogs(assetId.value)
    }
    
    saving.value = false
    uni.hideLoading()
    changeVisible.value = false
  } catch (e) {
    saving.value = false
    uni.hideLoading()
  }
}

const openPrint = () => {
  printVisible.value = true
}

const getQrUrl = (item: any) => {
  const text = item.asset_code || 'ERROR'
  return `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(text)}`
}

const executePrint = () => {
  printAssetLabel(detail.value)
}

// ---- 人员选择后调用的回调 ----
const confirmReassign = (emp: any) => {
  // 如果当前弹窗开着，更新弹窗内的临时人员
  if (changeVisible.value) {
    pendingOwner.value = emp
    // 方案 A 联动：如果选了人，且当前选的是闲置，自动切到“在用”
    if (pendingStatus.value === '闲置' && emp) {
      pendingStatus.value = '在用'
    }
  } else {
    // 如果弹窗没开（备选），直接走老逻辑（通常不会发生，除非代码触发）
    detail.value.owner = emp
  }
}

const navToTransferApply = () => {
  uni.navigateTo({ 
    url: `/pages/asset/transfer_apply?id=${assetId.value}&code=${detail.value.asset_code}&loc_id=${detail.value.location_id}&loc_name=${detail.value.location?.name || ''}` 
  })
}

onLoad((options: any) => {
  if (options && options.id) {
    assetId.value = options.id
    if (options.tab) {
      currentTab.value = options.tab
    }
    loadDetail(options.id)
    if (currentTab.value === 'logs') {
      loadLogs(options.id)
    }
  }
})

onMounted(() => {
  uni.$on('employee_selected', confirmReassign)
})

onUnmounted(() => {
  uni.$off('employee_selected', confirmReassign)
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
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  color: #999;
  gap: 12px;
  
  .err-icon { font-size: 40px; }
  .err-text { font-size: 13px; color: #999; text-align: center; padding: 0 20px; line-height: 1.6; }
  
  .retry-btn {
    margin-top: 8px;
    background: #1677ff;
    border-radius: 20px;
    padding: 8px 24px;
    
    .retry-text { color: #fff; font-size: 14px; }
  }
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

.tab-strip {
  display: flex;
  background: #fff;
  padding: 0 20px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 15px;
  
  .tab-item {
    padding: 12px 16px;
    font-size: 15px;
    color: #666;
    position: relative;
    margin-right: 15px;
    
    &.active {
      color: #007aff;
      font-weight: 600;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 30%;
        width: 40%;
        height: 3px;
        background: #007aff;
        border-radius: 2px;
      }
    }
  }
}

.section {
  background: #fff;
  border-radius: 14px;
  margin: 0 15px 15px;
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

.logs-container {
  padding: 10px 20px;
  background: #fff;
  margin: 0 15px 15px;
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  
  .empty-logs {
    padding: 30px 0;
    text-align: center;
    color: #999;
    font-size: 14px;
  }
  
  .log-item {
    display: flex;
    position: relative;
    padding-bottom: 20px;
    
    &:last-child {
      padding-bottom: 0;
      .log-line { display: none; }
    }
    
    .log-timeline {
      width: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-right: 12px;
      
      .log-dot {
        width: 10px;
        height: 10px;
        background: #007aff;
        border-radius: 50%;
        margin-top: 5px;
        border: 2px solid #e6f1ff;
      }
      
      .log-line {
        flex: 1;
        width: 1px;
        background: #eee;
        margin-top: 4px;
      }
    }
    
    .log-content {
      flex: 1;
      
      .log-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
        
        .log-action { font-size: 15px; font-weight: 600; color: #333; }
        .log-date { font-size: 12px; color: #999; }
      }
      
      .log-detail {
        font-size: 13px;
        color: #666;
        margin-bottom: 2px;
      }
      
      .log-memo {
        font-size: 12px;
        color: #888;
        background: #f9f9f9;
        padding: 6px 10px;
        border-radius: 6px;
        margin-top: 6px;
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
    
    &.info {
      background: #39c5bb;
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
  display: flex;
  flex-direction: column;
  max-height: 85vh;
  
  .dialog-header {
    display: flex;
    justify-content: space-between;
    padding: 15px;
    border-bottom: 1px solid #eee;
    flex-shrink: 0;
    
    .title { font-size: 16px; font-weight: bold; color: #333; }
    .close { font-size: 18px; color: #999; }
  }

  .change-body-scroll {
    flex: 1;
    max-height: 50vh;
    overflow-y: auto;
  }
  
  .dialog-body {
    padding: 20px;
    display: flex;
    justify-content: center;
    background: #f5f5f5;
  }
  
  .dialog-footer {
    padding: 15px 15px 25px; // 增加底部安全间距
    border-top: 1px solid #eee;
    flex-shrink: 0; // 强制不收缩，保证按钮完整
    
    .submit-btn, .print-btn {
      background: #1a73e8;
      color: #fff;
      border-radius: 22px;
      height: 44px;
      line-height: 44px;
      font-size: 16px;
      font-weight: 600;
      width: 100%;
      &::after { border: none; }
      &:active { opacity: 0.8; }
    }
  }
}

/* 综合变更样式 */
.change-body {
  padding: 30rpx;
}
.change-item {
  margin-bottom: 30rpx;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #efefef;
  padding-bottom: 20rpx;
}
.c-label {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 10rpx;
}
.c-val {
  font-size: 32rpx;
  color: #1a73e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 50rpx;
}
.placeholder {
  color: #ccc !important;
}
.c-arrow {
  color: #ccc;
  font-size: 32rpx;
}
.tip-text {
  font-size: 24rpx;
  color: #ff9800;
  background: #fff8e1;
  padding: 10rpx 20rpx;
  border-radius: 8rpx;
  margin-top: 10rpx;
  margin-bottom: 20rpx;
}
.section-divider {
  font-size: 26rpx;
  color: #333;
  font-weight: bold;
  padding: 10rpx 0;
  border-left: 6rpx solid #1a73e8;
  padding-left: 15rpx;
  margin: 20rpx 0;
  background: #f0f7ff;
}
.c-input {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8rpx;
  padding: 12rpx 20rpx;
  font-size: 28rpx;
  color: #333;
}

/* 标签实体排版 */
.print-label-page {
  width: 280px;
  height: 200px;
  background: #fff;
  border: 1.5px solid #000;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: #000;
  box-sizing: border-box;
  padding: 6px;
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
    font-size: 11px;
    padding: 2px 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .print-title {
    text-align: center;
    font-size: 14px;
    font-weight: 900;
    height: 36px;
    letter-spacing: -0.5px;
  }
  
  .print-row {
    height: 26px;
  }
  
  .print-qr-column {
    width: 80px;
    text-align: center;
    vertical-align: middle;
    padding: 1px;
    
    .qr-img {
      width: 72px;
      height: 72px;
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
