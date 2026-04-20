<template>
  <view class="page-wrap">
    <!-- 顶部导航 -->
    <view class="nav-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="back-btn" @click="goBack">‹</view>
      <text class="title">{{ taskName || '盘点核对' }}</text>
      <view class="nav-right">
        <text class="nav-btn" @click="handleExport">导出</text>
        <text class="nav-btn" @click="loadAll">刷新</text>
      </view>
    </view>



    <!-- 盘点进度概览 -->
    <view class="stat-banner">
      <view class="stat-item">
        <text class="num">{{ finishedCount }}</text>
        <text class="label">已盘点</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="num">{{ totalCount - finishedCount }}</text>
        <text class="label">待盘点</text>
      </view>
    </view>

    <!-- 扫码区域 -->
    <view class="action-zone">
      <view class="scan-visual" :class="{ 'scanning-glow': isScanning }" @click="openCamera">
        <text class="scan-icon">📡</text>
        <text class="scan-text">{{ isScanning ? '处理中...' : '请按 PDA 扫描键 或 点击此处扫码' }}</text>
      </view>
    </view>

    <!-- 盘点记录列表 -->
    <view class="records-section">
      <view class="records-title">盘点明细（共 {{ recentSuccess.length }} 条）</view>
      <scroll-view scroll-y :style="{ height: listHeight + 'px' }">
        <view class="record-item" v-for="(item, index) in recentSuccess" :key="index">
          <view class="dot"></view>
          <view class="info">
            <view class="row">
              <text class="code">{{ item.asset_code }}</text>
              <text class="name">{{ item.asset_name }}</text>
            </view>
            <text class="time">{{ item.status }} | {{ item.time }}</text>
          </view>
          <text :class="['tag', item.status === '已盘点' ? 'done' : 'wait']">
            {{ item.status === '已盘点' ? '✓' : '○' }}
          </text>
        </view>
        <view class="empty-hint" v-if="recentSuccess.length === 0 && !isScanning">
          <text>暂无盘点记录，请创建盘点任务或刷新</text>
        </view>
      </scroll-view>
    </view>

    <!-- 错误弹窗 -->
    <view class="error-mask" v-if="errorMsg" @click="errorMsg = ''">
      <view class="error-box" @click.stop>
        <text class="err-icon">❌</text>
        <text class="err-text">{{ errorMsg }}</text>
        <button class="err-btn" @click="errorMsg = ''">知道了</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad, onShow, onHide, onUnload } from '@dcloudio/uni-app'
import request from '@/utils/request'
import { startPDAListener, stopPDAListener } from '@/utils/pda'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 20)
const taskId = ref('')
const taskName = ref('')
const totalCount = ref(0)
const finishedCount = ref(0)
const isScanning = ref(false)
const errorMsg = ref('')
const recentSuccess = ref<any[]>([])
// 动态计算列表高度：屏幕高度 - 顶部导航 - 进度条 - 扫码区域 - 标题
const listHeight = ref(300)
const { windowHeight } = uni.getSystemInfoSync()
listHeight.value = Math.max(200, windowHeight - statusBarHeight.value - 50 - 180 - 120 - 50)

onLoad((options: any) => {
  if (options && options.id) {
    taskId.value = String(options.id).trim()
    taskName.value = decodeURIComponent(options.name || '正在盘点')
    loadAll()
  }
})

const loadAll = async () => {
  await loadTaskStatus()
  await loadFinishedRecords()
}

const loadTaskStatus = async () => {
  try {
    const res: any[] = await request.get('/inventory/tasks')
    const list = Array.isArray(res) ? res : []
    const current = list.find((t: any) => String(t.id) === taskId.value)
    if (current) {
      totalCount.value = current.total_count || 0
      finishedCount.value = current.finished_count || 0
    }
  } catch (e: any) {
    console.error('任务加载失败', e)
  }
}

const loadFinishedRecords = async () => {
  if (!taskId.value) return
  isScanning.value = true
  try {
    const res: any = await request.get(`/inventory/tasks/${taskId.value}/records`)
    const data: any[] = Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : [])
    
    recentSuccess.value = data.map((r: any) => ({
      asset_code: r.asset_code || r.asset_id || '无编号',
      asset_name: r.asset_name || '未命名',
      status: r.status || '未知',
      time: r.audit_time ? String(r.audit_time).split('T')[1]?.split('.')[0] || '—' : '—'
    }))
    
    recentSuccess.value.sort((a, b) => {
      if (a.status === '已盘点' && b.status !== '已盘点') return -1
      if (a.status !== '已盘点' && b.status === '已盘点') return 1
      return 0
    })
    
  } catch (e: any) {
    errorMsg.value = `加载记录失败\n${e?.data?.detail || e?.errMsg || JSON.stringify(e).substring(0, 80)}`
  } finally {
    isScanning.value = false
  }
}

const handleExport = () => {
  const baseUrl = uni.getStorageSync('itom_server_url') || ''
  const token = uni.getStorageSync('itom_token') || ''
  const exportUrl = `${baseUrl}/inventory/tasks/${taskId.value}/export?token=${token}`

  uni.showLoading({ title: '正在生成报表...' })
  
  uni.downloadFile({
    url: exportUrl,
    header: {
      'Authorization': `Bearer ${token}`
    },
    success: (res) => {
      if (res.statusCode === 200) {
        uni.hideLoading()
        uni.showModal({
          title: '导出完成',
          content: '报表已生成，是否立即打开预览？',
          success: (confirmRes) => {
            if (confirmRes.confirm) {
              uni.openDocument({
                filePath: res.tempFilePath,
                fileType: 'xlsx',
                success: () => console.log('打开文档成功'),
                fail: (err) => {
                  uni.showToast({ title: '打开预览失败，请手动查找文件', icon: 'none' })
                }
              })
            }
          }
        })
      } else {
        uni.hideLoading()
        uni.showToast({ title: '导出失败，请重试', icon: 'none' })
      }
    },
    fail: (err) => {
      uni.hideLoading()
      uni.showToast({ title: '网络请求失败', icon: 'none' })
    }
  })
}

const handleBarcode = async (code: string) => {
  if (!code || !taskId.value) return
  isScanning.value = true
  
  try {
    await request.post(`/inventory/tasks/${taskId.value}/submit`, { asset_code: code })
    uni.vibrateShort()
    uni.showToast({ title: '核对成功', icon: 'success', duration: 1000 })
    // 扫码后强制刷新
    await loadAll()
  } catch (e: any) {
    const detail = e?.data?.detail || '核对失败，请检查资产编码'
    errorMsg.value = detail
    uni.vibrateLong()
  } finally {
    isScanning.value = false
  }
}

const openCamera = () => {
  uni.scanCode({
    onlyFromCamera: true,
    success: (res) => handleBarcode(res.result),
    fail: () => {}
  })
}

const goBack = () => uni.navigateBack()

onShow(() => {
  startPDAListener((code) => handleBarcode(code))
})

onHide(() => stopPDAListener())
onUnload(() => stopPDAListener())
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #f7f9fc;
}

.nav-header {
  background: #fff;
  padding-bottom: 12px;
  padding-left: 4px;
  padding-right: 15px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #efefef;
  .back-btn { width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; font-size: 28px; color: #333; }
  .title { flex: 1; font-size: 16px; font-weight: 600; color: #333; text-align: center; }
  .nav-right {
    display: flex;
    gap: 12px;
  }
  .nav-btn { font-size: 14px; color: #1677ff; }
}


.stat-banner {
  display: flex;
  background: linear-gradient(135deg, #1677ff, #4fa3ff);
  margin: 15px;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 4px 15px rgba(22, 119, 255, 0.2);
  .stat-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    .num { font-size: 28px; font-weight: bold; color: #fff; }
    .label { font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 4px; }
  }
  .stat-divider { width: 1px; height: 30px; background: rgba(255,255,255,0.2); align-self: center; }
}

.action-zone {
  padding: 0 15px 15px;
  .scan-visual {
    height: 120px;
    background: #fff;
    border-radius: 14px;
    border: 2px dashed #d9d9d9;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    &.scanning-glow { border-color: #1677ff; background: #e6f7ff; }
    .scan-icon { font-size: 36px; }
    .scan-text { font-size: 13px; color: #666; }
  }
}

.records-section {
  margin: 0 15px 15px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  .records-title {
    font-size: 13px;
    font-weight: 600;
    color: #666;
    padding: 12px 15px;
    border-bottom: 1px solid #f5f5f5;
    background: #fafafa;
  }
}

.record-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #f9f9f9;
  .dot { width: 6px; height: 6px; background: #52c41a; border-radius: 50%; margin-right: 12px; flex-shrink: 0; }
  .info {
    flex: 1;
    .row { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
    .code { font-size: 14px; font-weight: 600; color: #1a1a1a; }
    .name { font-size: 11px; color: #888; background: #f5f5f5; padding: 1px 6px; border-radius: 3px; }
    .time { font-size: 11px; color: #bbb; }
  }
  .tag {
    font-size: 16px;
    flex-shrink: 0;
    &.done { color: #52c41a; }
    &.wait { color: #d9d9d9; }
  }
}

.empty-hint {
  padding: 40px 20px;
  text-align: center;
  color: #bbb;
  font-size: 13px;
}

.error-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.65);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px;
}

.error-box {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  .err-icon { font-size: 44px; margin-bottom: 14px; }
  .err-text { font-size: 14px; color: #333; text-align: center; margin-bottom: 20px; line-height: 1.6; }
  .err-btn {
    width: 60%; height: 44px; background: #333; color: #fff;
    border-radius: 22px; font-size: 15px;
    &::after { border: none; }
  }
}
</style>
