<template>
  <view class="page-wrap">
    <!-- 自定义顶部 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <text class="nav-title">扫描资产</text>
    </view>

    <view class="scan-container">
      <view class="scan-tips">
        <text class="tips-text">请将资产上的二维码或条形码对准扫描框</text>
      </view>

      <view class="scan-box" @click="startScan">
        <view class="scan-frame">
          <view class="corner tl"></view>
          <view class="corner tr"></view>
          <view class="corner bl"></view>
          <view class="corner br"></view>
          <view class="scan-line" :class="{ scanning: isScanning }"></view>
          <text class="scan-icon">📷</text>
        </view>
      </view>

      <view class="scan-actions">
        <view class="scan-btn secondary" @click="manualInput">
          <text class="btn-text">手动输入资产编码</text>
        </view>
      </view>
    </view>

    <!-- 手动输入弹窗 -->
    <view class="modal-mask" v-if="showInputModal" @click.self="showInputModal = false">
      <view class="modal-box">
        <text class="modal-title">手动输入资产编码</text>
        <input
          class="modal-input"
          v-model="manualCode"
          placeholder="请输入资产编码"
          focus
        />
        <view class="modal-actions">
          <view class="modal-btn cancel" @click="showInputModal = false">取消</view>
          <view class="modal-btn confirm" @click="goByCode">查询</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import request from '@/utils/request'

const statusBarHeight = ref(20)
try {
  statusBarHeight.value = uni.getSystemInfoSync().statusBarHeight || 20
} catch (e) {}

const isScanning = ref(false)
const showInputModal = ref(false)
const manualCode = ref('')

import { onShow, onHide, onUnload } from '@dcloudio/uni-app'
import { startPDAListener, stopPDAListener } from '@/utils/pda'

// 核心处理函数：解析扫码结果并跳转
const handleScanResult = async (code: string) => {
  if (!code) return
  
  // 1. 智能解构查询码
  let queryCode = code
  if (code.includes('/mobile/asset/')) {
    // 标准 Token URL 格式
    queryCode = code.split('/mobile/asset/')[1].split(/[/?#]/)[0]
  } else if (code.startsWith('http')) {
    // 其它 URL 格式兜底
    const parts = code.split('/')
    const lastPart = parts[parts.length - 1]
    if (lastPart && !lastPart.includes(':')) {
      queryCode = lastPart
    }
  }

  // 2. 发起原子化查询
  try {
    const asset = await request.get(`/assets/mobile/${queryCode}`)
    if (asset && asset.id) {
      uni.navigateTo({ url: `/pages/asset/detail?id=${asset.id}` })
      return true
    }
  } catch (e) {
    // 404 会由请求拦截器报错
  }
  return false
}

const startScan = async () => {
  if (isScanning.value) return
  isScanning.value = true
  
  try {
    const res = await uni.scanCode({ onlyFromCamera: true })
    if (res && res.result) {
      await handleScanResult(res.result)
    }
  } catch (e: any) {
    if (e && e.errMsg && e.errMsg.includes('cancel')) {
       // 用户主动取消
    } else {
       uni.showToast({ title: '扫描异常，请重试', icon: 'none' })
    }
  } finally {
    isScanning.value = false
  }
}

const manualInput = () => {
  manualCode.value = ''
  showInputModal.value = true
}

const goByCode = async () => {
  if (!manualCode.value.trim()) return
  showInputModal.value = false
  try {
    const list = await request.get('/assets/', { keyword: manualCode.value.trim(), limit: 3 })
    if (list && list.length > 0) {
      uni.navigateTo({ url: `/pages/asset/detail?id=${list[0].id}` })
    } else {
      uni.showToast({ title: '未找到资产：' + manualCode.value, icon: 'none', duration: 2500 })
    }
  } catch (e) {
    uni.showToast({ title: '查询失败', icon: 'none' })
  }
}

onShow(() => {
  // 1. 自动开启摄像头（可选，根据用户习惯）
  setTimeout(() => {
    // startScan() // 如果用户希望进场即扫，取消此行注释
  }, 300)

  // 2. 启动 PDA 硬件扫描枪监听
  startPDAListener((code) => {
    handleScanResult(code)
  })
})

onHide(() => {
  stopPDAListener()
})

onUnload(() => {
  stopPDAListener()
})
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: 12px;
  
  .nav-title {
    font-size: 17px;
    font-weight: 600;
    color: #fff;
  }
}

.scan-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.scan-tips {
  margin-bottom: 24px;
  .tips-text { font-size: 14px; color: rgba(255,255,255,0.7); }
}

.scan-box {
  width: 260px;
  height: 260px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40px;
}

.scan-frame {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .scan-icon {
    font-size: 64px;
    opacity: 0.3;
  }
}

.corner {
  position: absolute;
  width: 24px;
  height: 24px;
  border-color: #1677ff;
  border-style: solid;
  
  &.tl { top: 0; left: 0; border-width: 3px 0 0 3px; }
  &.tr { top: 0; right: 0; border-width: 3px 3px 0 0; }
  &.bl { bottom: 0; left: 0; border-width: 0 0 3px 3px; }
  &.br { bottom: 0; right: 0; border-width: 0 3px 3px 0; }
}

.scan-line {
  position: absolute;
  left: 10px;
  right: 10px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #1677ff, transparent);
  top: 30px;
  
  &.scanning {
    animation: scan-move 1.5s linear infinite;
  }
}

@keyframes scan-move {
  0% { top: 10px; }
  100% { top: 240px; }
}

.scan-actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  
  .scan-btn {
    height: 48px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &.primary { background: #1677ff; }
    &.secondary { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); }
    
    .btn-text { font-size: 15px; color: #fff; }
  }
}

/* 弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-box {
  background: #fff;
  border-radius: 14px;
  padding: 24px 20px;
  width: 300px;
  
  .modal-title {
    font-size: 16px;
    font-weight: 600;
    color: #1a1a1a;
    display: block;
    margin-bottom: 16px;
    text-align: center;
  }
  
  .modal-input {
    width: 100%;
    height: 44px;
    background: #f5f7fa;
    border-radius: 8px;
    padding: 0 12px;
    font-size: 14px;
    color: #333;
    box-sizing: border-box;
    border: 1px solid #e8e8e8;
  }
  
  .modal-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
    
    .modal-btn {
      flex: 1;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      
      &.cancel { background: #f5f5f5; color: #666; }
      &.confirm { background: #1677ff; color: #fff; }
    }
  }
}
</style>
