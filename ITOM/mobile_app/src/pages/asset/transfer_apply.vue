<template>
  <view class="container">
    <view class="header">
      <text class="title">跨归属地调拨申请</text>
      <text class="subtitle">发起后需集团超级管理员审批</text>
    </view>

    <view class="form-card shadow-sm">
      <view class="asset-brief bg-blue-50">
        <text class="label">待调拨资产</text>
        <view class="asset-info">
          <text class="asset-code font-bold">{{ assetCode }}</text>
        </view>
        <view class="loc-tags">
          <text class="tag current">{{ fromLocName }}</text>
          <text class="tag divider">➔</text>
          <text class="tag target">{{ selectedLocName || '选择目的地' }}</text>
        </view>
      </view>

      <view class="form-item border-b">
        <text class="item-label">目标归属地</text>
        <picker mode="selector" :range="locationNames" @change="onLocChange">
          <view class="picker-val">
            <text v-if="selectedLocName">{{ selectedLocName }}</text>
            <text v-else class="placeholder">请选择目标子公司/分部</text>
            <text class="arrow">›</text>
          </view>
        </picker>
      </view>

      <view class="form-item mt-4">
        <text class="item-label">调拨原因说明</text>
        <textarea 
          class="memo-area" 
          v-model="memo" 
          placeholder="请简要说明此次跨区调拨的原因，如：业务借调、地点搬迁等..." 
          maxlength="200"
        />
      </view>
    </view>

    <view class="tips">
      <text class="tip-title">调拨说明：</text>
      <text class="tip-content">1. 调拨申请发起后，资产将进入“待审批”状态。</text>
      <text class="tip-content">2. 审批通过后，由源归属地管理员发货并填写物流单号。</text>
      <text class="tip-content">3. 目标归属地管理员收到资产后点击签收，流程结束。</text>
    </view>

    <view class="footer">
      <button class="submit-btn shadow" :loading="submitting" @click="doSubmit">提交调拨申请</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/utils/request'

const assetId = ref('')
const assetCode = ref('')
const fromLocId = ref(0)
const fromLocName = ref('')
const memo = ref('')

const locations = ref<any[]>([])
const locationNames = ref<string[]>([])
const selectedLocIndex = ref(-1)
const selectedLocName = ref('')
const submitting = ref(false)

const loadLocations = async () => {
  try {
    const res = await request.get('/locations/')
    // 过滤掉当前归属地
    locations.value = (res || []).filter((l: any) => l.id !== fromLocId.value && l.is_active)
    locationNames.value = locations.value.map(l => l.name)
  } catch (e) {}
}

const onLocChange = (e: any) => {
  selectedLocIndex.value = e.detail.value
  selectedLocName.value = locationNames.value[e.detail.value]
}

const doSubmit = async () => {
  if (selectedLocIndex.value === -1) {
    return uni.showToast({ title: '请选择目标归属地', icon: 'none' })
  }
  if (!memo.value) {
    return uni.showToast({ title: '请填写调拨原因', icon: 'none' })
  }

  submitting.value = true
  try {
    await request.post('/transfers/', {
      asset_id: assetId.value,
      to_location_id: locations.value[selectedLocIndex.value].id,
      memo: memo.value
    })
    uni.showToast({ title: '申请已提交', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (e) {
    // 错误在 request 中已通过 toast 显示
  } finally {
    submitting.value = false
  }
}

onLoad((options: any) => {
  if (options) {
    assetId.value = options.id
    assetCode.value = options.code
    fromLocId.value = parseInt(options.loc_id)
    fromLocName.value = options.loc_name
    loadLocations()
  }
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f8fafc;
  padding: 20px;
}

.header {
  margin-bottom: 24px;
  .title { font-size: 24px; font-weight: bold; color: #1e293b; display: block; }
  .subtitle { font-size: 14px; color: #64748b; margin-top: 4px; display: block; }
}

.form-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 24px;
}

.asset-brief {
  padding: 20px;
  border-bottom: 1px dashed #e2e8f0;
  
  .label { font-size: 12px; color: #64748b; margin-bottom: 8px; display: block; }
  .asset-code { font-size: 18px; color: #1a73e8; display: block; margin-bottom: 12px; }
  
  .loc-tags {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .tag {
      font-size: 14px;
      padding: 4px 12px;
      border-radius: 8px;
      
      &.current { background: #f1f5f9; color: #475569; }
      &.target { background: #ecfdf5; color: #059669; font-weight: bold; }
      &.divider { color: #cbd5e1; }
    }
  }
}

.form-item {
  padding: 16px 20px;
  
  .item-label { font-size: 15px; font-weight: 600; color: #334155; margin-bottom: 12px; display: block; }
  
  .picker-val {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 48px;
    background: #f8fafc;
    border-radius: 12px;
    padding: 0 16px;
    border: 1px solid #f1f5f9;
    
    .placeholder { color: #94a3b8; font-size: 14px; }
    .arrow { color: #cbd5e1; font-size: 20px; }
  }
}

.memo-area {
  width: 100%;
  height: 120px;
  background: #f8fafc;
  border-radius: 12px;
  padding: 12px;
  font-size: 14px;
  border: 1px solid #f1f5f9;
  box-sizing: border-box;
}

.tips {
  padding: 0 10px;
  .tip-title { font-size: 14px; font-weight: bold; color: #64748b; display: block; margin-bottom: 8px; }
  .tip-content { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px; line-height: 1.6; }
}

.footer {
  position: fixed;
  bottom: 30px;
  left: 20px;
  right: 20px;
  
  .submit-btn {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    color: #fff;
    height: 54px;
    line-height: 54px;
    border-radius: 27px;
    font-size: 16px;
    font-weight: bold;
    &::after { border: none; }
  }
}

.shadow-sm { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
.shadow { box-shadow: 0 10px 15px -3px rgba(26, 115, 232, 0.3), 0 4px 6px -2px rgba(26, 115, 232, 0.05); }
</style>
