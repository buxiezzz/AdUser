<template>
  <view class="page-wrap">
    <!-- 自定义顶部导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <text class="nav-title">资产台账</text>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <text class="search-icon">🔍</text>
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索资产编码/序列号..."
          placeholder-class="search-placeholder"
          confirm-type="search"
          @confirm="onSearch"
        />
      </view>
      <view class="search-refresh" @click="onRefresh">
        <text class="refresh-icon">⟳</text>
      </view>
    </view>

    <!-- 统计 + 批量操作区 -->
    <view class="stat-bar">
      <view class="stat-left">
        <text class="stat-total">总计 {{ total }} 条资产</text>
      </view>
      
      <view class="stat-right">
        <!-- 常规模式：点此进入批量 -->
        <view class="mini-btn-link" v-if="!isBatchMode" @click="startBatchMode">
          <text class="btn-text">批量操作</text>
        </view>
        
        <!-- 批量模式：操作组 -->
        <view class="batch-ops-group" v-else>
          <text class="op-link" @click="toggleSelectAll">{{ isAllSelected ? '取消' : '全选' }}</text>
          <view class="op-divider"></view>
          <view class="print-trigger-btn" @click="executeBatchPrint">
            <text class="print-btn-text">批量打印({{ selectedIds.length }})</text>
          </view>
          <view class="op-divider"></view>
          <text class="op-link cancel" @click="exitBatchMode">退出</text>
        </view>
      </view>
    </view>

    <!-- 状态标签页 -->
    <scroll-view scroll-x class="tab-scroll" :show-scrollbar="false">
      <view class="tab-bar">
        <view
          class="tab-item"
          v-for="tab in statusTabs"
          :key="tab.value"
          :class="{ active: activeTab === tab.value }"
          @click="switchTab(tab.value)"
        >
          <text class="tab-text">{{ tab.label }}</text>
          <view class="tab-line" v-if="activeTab === tab.value"></view>
        </view>
      </view>
    </scroll-view>

    <!-- 资产列表 -->
    <scroll-view
      scroll-y
      class="list-scroll"
      @scrolltolower="loadMore"
      lower-threshold="80"
    >
      <view 
        class="asset-card" 
        v-for="item in assetList" 
        :key="item.id"
        :class="{ 'card-hover': !isBatchMode, 'is-selected': isSelected(item.id) }"
        @tap="handleCardTap(item)"
      >
        <!-- 批量选择勾选框 -->
        <view class="batch-checkbox" v-if="isBatchMode">
          <view class="checkbox-circle" :class="{ checked: isSelected(item.id) }">
            <text v-if="isSelected(item.id)" class="check-icon">✓</text>
          </view>
        </view>

        <view class="card-content-wrap">
          <!-- 卡片顶部：分类名 + 状态 -->
          <view class="card-top">
            <text class="card-category">{{ item.category?.name || '未知分类' }}</text>
            <text :class="['card-status', statusClass(item.status)]">{{ item.status }}</text>
          </view>
          <!-- 卡片主体：图片 + 信息 -->
          <view class="card-body">
            <view class="card-img">
              <text class="img-placeholder">🖼</text>
            </view>
            <view class="card-info">
              <view class="info-row">
                <text class="info-label">资产编码：</text>
                <text class="info-value">{{ item.asset_code }}</text>
              </view>
              <view class="info-row">
                <text class="info-label">使用人：</text>
                <text class="info-value">{{ item.owner?.name || '-' }}</text>
              </view>
              <view class="info-row" v-if="getFirstAttr(item)">
                <text class="info-label">{{ getFirstAttr(item)?.key }}：</text>
                <text class="info-value">{{ getFirstAttr(item)?.val }}</text>
              </view>
            </view>
          </view>
          <!-- 卡片操作按钮 (非批量模式显示) -->
          <view class="card-actions" v-if="!isBatchMode">
            <view class="action-btn" hover-class="btn-hover" @tap.stop="goToDetail(item.id)">
              <text class="action-text">资产管理</text>
            </view>
            <view class="action-divider"></view>
            <view class="action-btn" hover-class="btn-hover" @tap.stop="goToLogs(item.id)">
              <text class="action-text">操作记录</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 加载状态 -->
      <view class="list-status" v-if="loading">
        <text class="status-text">加载中...</text>
      </view>
      <view class="list-status" v-else-if="!loading && assetList.length === 0">
        <text class="status-text">暂无资产数据</text>
      </view>
      <view class="list-status" v-else-if="!hasMore">
        <text class="status-text">— 没有更多了 —</text>
      </view>
      <!-- 底部留白 -->
      <view style="height: 140rpx;"></view>
    </scroll-view>

    <!-- 只有在非批量模式下才显示通用导航栏 -->
    <CustomTabBar v-if="!isBatchMode" :activeIndex="1" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow, onHide, onUnload } from '@dcloudio/uni-app'
import request from '@/utils/request'
import { startPDAListener, stopPDAListener } from '@/utils/pda'
import { printBatchAssets } from '@/utils/printer'
import CustomTabBar from '@/components/CustomTabBar.vue'

// 批量模式状态
const isBatchMode = ref(false)
const selectedIds = ref<string[]>([])

const isSelected = (id: string) => selectedIds.value.includes(id)
const isAllSelected = computed(() => assetList.value.length > 0 && selectedIds.value.length === assetList.value.length)

// 切换批量模式
const startBatchMode = () => {
  isBatchMode.value = true
  selectedIds.value = []
}
const exitBatchMode = () => {
  isBatchMode.value = false
  selectedIds.value = []
}

// 点击卡片处理
const handleCardTap = (item: any) => {
  if (isBatchMode.value) {
    const idx = selectedIds.value.indexOf(item.id)
    if (idx > -1) {
      selectedIds.value.splice(idx, 1)
    } else {
      selectedIds.value.push(item.id)
    }
  } else {
    goToDetail(item.id)
  }
}

// 全选/取消
const toggleSelectAll = () => {
  if (selectedIds.value.length === assetList.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = assetList.value.map(item => item.id)
  }
}

// 执行批量打印
const executeBatchPrint = () => {
  if (selectedIds.value.length === 0) {
    uni.showToast({ title: '请先勾选资产', icon: 'none' })
    return
  }
  
  uni.showModal({
    title: '批量打印确认',
    content: `确定要打印选中的 ${selectedIds.value.length} 个资产标签吗？`,
    success: (res) => {
      if (res.confirm) {
        // 根据 ID 找出完整的资产对象列表
        const targets = assetList.value.filter(item => selectedIds.value.includes(item.id))
        printBatchAssets(targets)
      }
    }
  })
}

// 系统状态栏高度
const statusBarHeight = ref(20)
try {
  const sysInfo = uni.getSystemInfoSync()
  statusBarHeight.value = sysInfo.statusBarHeight || 20
} catch (e) {}

// 状态标签
const statusTabs = [
  { label: '全部', value: '' },
  { label: '闲置', value: '闲置' },
  { label: '在用', value: '在用' },
  { label: '维修', value: '维修' },
  { label: '报废', value: '报废' },
]
const activeTab = ref('')

// 页面显示时检查是否有外部传入的过滤状态
onShow(() => {
  uni.hideTabBar()
  // PDA 扫描枪监听逻辑
  startPDAListener((code) => {
    if (code) {
      keyword.value = code
      uni.vibrateShort()
      loadData(true)
    }
  })

  const status = uni.getStorageSync('active_asset_status')
  if (status !== undefined && status !== null) {
    activeTab.value = status
    loadData(true)
    uni.removeStorageSync('active_asset_status')
  } else {
    // 默认进入也加载一次
    loadData(true)
  }
})

onHide(() => stopPDAListener())
onUnload(() => stopPDAListener())

// 数据状态
const keyword = ref('')
const assetList = ref<any[]>([])
const loading = ref(false)
const hasMore = ref(true)
const skip = ref(0)
const total = ref(0)
const limit = 20

// 排序
const sortOptions = ['更新时间最近', '更新时间最早', '编码升序', '编码降序']
const sortIndex = ref(0)
const sortLabel = computed(() => sortOptions[sortIndex.value])

const toggleSort = () => {
  sortIndex.value = (sortIndex.value + 1) % sortOptions.length
  loadData(true)
}

// 加载数据
const loadData = async (reset = false) => {
  if (reset) {
    skip.value = 0
    assetList.value = []
    hasMore.value = true
    total.value = 0
  }
  if (!hasMore.value || loading.value) return

  loading.value = true
  try {
    const params: any = {
      skip: skip.value,
      limit,
      sort_by: 'updated_at',
      order: 'desc'
    }
    if (keyword.value) params.keyword = keyword.value
    if (activeTab.value) params.status = activeTab.value

    const res = await request.get('/assets/', params)
    if (res && res.length > 0) {
      assetList.value.push(...res)
      skip.value += limit
      if (res.length < limit) hasMore.value = false
    } else {
      hasMore.value = false
    }
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '加载失败，请重试', icon: 'none', duration: 2000 })
  } finally {
    loading.value = false
  }
}

// 获取资产总数（支持过滤条件的真实总数）
const fetchTotal = async () => {
  try {
    const params: any = { skip: 0, limit: 99999 } // 请求很大范围以获取总数
    if (keyword.value) params.keyword = keyword.value
    if (activeTab.value) params.status = activeTab.value
    
    const res = await request.get('/assets/', params)
    if (res) total.value = res.length
  } catch (e) {}
}

const onSearch = () => loadData(true)
const onRefresh = () => {
  keyword.value = ''
  loadData(true)
  fetchTotal()
}
const loadMore = () => loadData()
const switchTab = (val: string) => {
  activeTab.value = val
  loadData(true)
}

const getFirstAttr = (item: any) => {
  if (!item.dynamic_attributes) return null
  const keys = Object.keys(item.dynamic_attributes)
  if (keys.length === 0) return null
  const k = keys[0]
  return { key: k, val: item.dynamic_attributes[k] }
}

const statusClass = (s: string) => {
  if (s === '在用') return 'status-active'
  if (s === '闲置') return 'status-idle'
  if (s === '维修') return 'status-repair'
  if (s === '报废') return 'status-scrap'
  return 'status-idle'
}

// 导航动作
const goToDetail = (id: string) => {
  if (!id) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  uni.showLoading({ title: '正在跳转...', mask: true })
  uni.navigateTo({ 
    url: `/pages/asset/detail?id=${id}`,
    complete: () => { uni.hideLoading() }
  })
}
const goToLogs = (id: string) => {
  if (!id) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  uni.showLoading({ title: '加载中...', mask: true })
  uni.navigateTo({ 
    url: `/pages/asset/detail?id=${id}&tab=logs`,
    complete: () => { uni.hideLoading() }
  })
}
const goToCreate = () => {
  uni.navigateTo({ url: '/pages/asset/create' })
}
const goToAllLogs = () => {
  uni.showToast({ title: '全部操作记录', icon: 'none', duration: 1500 })
}
const showFilter = () => {
  uni.showToast({ title: '筛选功能开发中', icon: 'none', duration: 1500 })
}

onMounted(() => {
  // 监听全局事件，用于获取更实时的 Tab 切换指令
  uni.$on('refreshAssetList', (data : any) => {
    activeTab.value = data.status || ''
    loadData(true)
  })
  
  loadData(true)
  fetchTotal()
})

onUnmounted(() => {
  uni.$off('refreshAssetList')
})
</script>

<style lang="scss" scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
}

/* ===== 顶部导航 ===== */
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  padding-bottom: 12px;
  padding-left: 16px;
  padding-right: 16px;
  position: relative;
  
  .nav-title {
    font-size: 17px;
    font-weight: 600;
    color: #1a1a1a;
    text-align: center;
  }
  
  .nav-action {
    position: absolute;
    right: 16px;
    bottom: 12px;
    font-size: 14px;
    color: #1677ff;
    font-weight: 500;
  }
}

/* ===== 搜索栏 ===== */
.search-bar {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: #fff;
  gap: 10px;
  
  .search-input-wrap {
    flex: 1;
    display: flex;
    align-items: center;
    background: #f4f5f7;
    border-radius: 22px;
    padding: 7px 14px;
    
    .search-icon {
      font-size: 14px;
      margin-right: 6px;
      color: #bbb;
    }
    
    .search-input {
      flex: 1;
      font-size: 14px;
      color: #333;
      background: transparent;
    }
    
    .search-placeholder {
      color: #ccc;
      font-size: 14px;
    }
  }
  
  .search-refresh {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #f0f6ff;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .refresh-icon {
      font-size: 20px;
      color: #1677ff;
    }
  }
}

/* ===== 统计栏 ===== */
.stat-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: #fff;
  border-top: 1px solid #f2f2f2;
  
  .stat-total {
    font-size: 12px;
    color: #888;
  }
  
  .stat-right {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .sort-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      
      .sort-text {
        font-size: 12px;
        color: #1677ff;
      }
      .sort-arrow {
        font-size: 10px;
        color: #1677ff;
      }
    }
    
    .filter-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border: 1px solid #e0e0e0;
      border-radius: 14px;
      
      .filter-icon {
        font-size: 13px;
        color: #555;
      }
      .filter-text {
        font-size: 12px;
        color: #555;
      }
    }
  }
}

/* ===== 状态标签 ===== */
.tab-scroll {
  background: #fff;
  white-space: nowrap;
}

.tab-bar {
  display: flex;
  flex-direction: row;
  padding: 0 10px;
  border-bottom: 1px solid #f2f2f2;
  
  .tab-item {
    flex-shrink: 0;
    padding: 10px 14px 0;
    position: relative;
    
    .tab-text {
      font-size: 14px;
      color: #888;
      line-height: 1;
    }
    
    .tab-line {
      height: 2px;
      background: #1677ff;
      border-radius: 2px;
      margin-top: 8px;
    }
    
    &.active .tab-text {
      color: #1677ff;
      font-weight: 600;
    }
  }
}

/* ===== 列表区域 ===== */
.list-scroll {
  flex: 1;
  height: 0;
  padding: 10px 12px;
  box-sizing: border-box;
}

.asset-card {
  background: #fff;
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  
  &.card-hover {
    background: #f0f6ff;
    transform: scale(0.98);
  }
  
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px 10px;
    border-bottom: 1px solid #f8f8f8;
    
    .card-category {
      font-size: 15px;
      font-weight: 600;
      color: #1a1a1a;
    }
    
    .card-status {
      font-size: 13px;
      font-weight: 500;
      
      &.status-active { color: #f5222d; }
      &.status-idle   { color: #1677ff; }
      &.status-borrow { color: #fa8c16; }
      &.status-repair { color: #faad14; }
      &.status-scrap  { color: #999; }
    }
  }
  
  .card-body {
    display: flex;
    padding: 10px 14px;
    align-items: flex-start;
    gap: 12px;
    
    .card-img {
      width: 60px;
      height: 54px;
      background: #f0f4ff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      .img-placeholder {
        font-size: 24px;
        opacity: 0.4;
      }
    }
    
    .card-info {
      flex: 1;
      
      .info-row {
        display: flex;
        margin-bottom: 5px;
        
        .info-label {
          width: 65px; /* 设为4个汉字的固定宽度 */
          font-size: 12px;
          color: #999;
          text-align: justify;
          text-align-last: justify; /* 实现分散对齐 */
          flex-shrink: 0;
        }
        .info-value {
          font-size: 12px;
          color: #333;
          flex: 1;
        }
      }
    }
  }
  
  .card-actions {
    display: flex;
    border-top: 1px solid #f5f5f5;
    
    .action-btn {
      flex: 1;
      padding: 10px 0;
      text-align: center;
      
      .action-text {
        font-size: 13px;
        color: #1677ff;
      }
      
      &.btn-hover {
        background: #f0f6ff;
        opacity: 0.8;
      }
    }
    
    .action-divider {
      width: 1px;
      background: #f0f0f0;
      margin: 8px 0;
    }
  }
}

.list-status {
  text-align: center;
  padding: 16px 0;
  
  .status-text {
    font-size: 12px;
    color: #ccc;
  }
}

/* ===== 统计 + 批量操作区 ===== */
.stat-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #f8f8f8;
  
  .stat-left {
    .stat-total {
      font-size: 13px;
      color: #999;
      font-weight: 500;
    }
  }
  
  .stat-right {
    display: flex;
    align-items: center;
    
    .mini-btn-link {
      padding: 4px 8px;
      background: #f0f6ff;
      border-radius: 4px;
      
      .btn-text {
        font-size: 12px;
        color: #1677ff;
        font-weight: 600;
      }
    }
    
    .batch-ops-group {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .op-link {
        font-size: 13px;
        color: #1677ff;
        font-weight: 600;
        
        &.cancel { color: #ff4d4f; }
      }
      
      .op-divider {
        width: 1px;
        height: 12px;
        background: #eee;
      }
      
      .print-trigger-btn {
        background: #1677ff;
        padding: 4px 12px;
        border-radius: 100px;
        box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
        
        .print-btn-text {
          font-size: 12px;
          color: #fff;
          font-weight: 700;
        }
        
        &:active {
          opacity: 0.8;
          transform: scale(0.95);
        }
      }
    }
  }
}

/* ===== 批量模式新增样式 ===== */
.asset-card {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  
  &.is-selected {
    border: 2px solid #1677ff;
    box-shadow: 0 4px 12px rgba(22, 119, 255, 0.15);
  }
}

.batch-checkbox {
  width: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-right: 1px solid #f0f0f0;
  
  .checkbox-circle {
    width: 22px;
    height: 22px;
    border: 2px solid #ddd;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &.checked {
      background: #1677ff;
      border-color: #1677ff;
    }
    
    .check-icon {
      color: #fff;
      font-size: 14px;
      font-weight: bold;
    }
  }
}

.card-content-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.bottom-btn {
  &.primary .bottom-text {
    color: #1677ff;
    font-weight: 700;
  }
  &.cancel .bottom-text {
    color: #ff4d4f;
  }
}
</style>
