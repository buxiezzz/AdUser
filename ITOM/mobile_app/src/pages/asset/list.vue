<template>
  <view class="page-wrap">
    <!-- 自定义顶部导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <text class="nav-title">资产列表</text>
      <text class="nav-action" @click="goToCreate">资产入库</text>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <text class="search-icon">🔍</text>
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索资产"
          placeholder-class="search-placeholder"
          confirm-type="search"
          @confirm="onSearch"
        />
      </view>
      <view class="search-refresh" @click="onRefresh">
        <text class="refresh-icon">⟳</text>
      </view>
    </view>

    <!-- 统计 + 排序 + 筛选 -->
    <view class="stat-bar">
      <text class="stat-total">总计 {{ total }} 条资产</text>
      <view class="stat-right">
        <view class="sort-btn" @click="toggleSort">
          <text class="sort-text">{{ sortLabel }}</text>
          <text class="sort-arrow">▼</text>
        </view>
        <view class="filter-btn" @click="showFilter">
          <text class="filter-icon">⊟</text>
          <text class="filter-text">筛选</text>
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
        hover-class="card-hover"
        @tap="goToDetail(item.id)"
      >
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
            <view class="info-row" v-if="getFirstAttr(item)">
              <text class="info-label">{{ getFirstAttr(item)?.key }}：</text>
              <text class="info-value">{{ getFirstAttr(item)?.val }}</text>
            </view>
            <view class="info-row" v-if="item.owner">
              <text class="info-label">使用人：</text>
              <text class="info-value">{{ item.owner.name }}</text>
            </view>
          </view>
        </view>
        <!-- 卡片操作按钮 -->
        <view class="card-actions">
          <view class="action-btn" hover-class="btn-hover" @tap.stop="goToDetail(item.id)">
            <text class="action-text">资产管理</text>
          </view>
          <view class="action-divider"></view>
          <view class="action-btn" hover-class="btn-hover" @tap.stop="goToLogs(item.id)">
            <text class="action-text">操作记录</text>
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
      <!-- 底部留白，防止被操作栏遮挡 -->
      <view style="height: 120rpx;"></view>
    </scroll-view>

    <!-- 底部固定操作栏 -->
    <view class="bottom-bar">
      <view class="bottom-btn" @click="goToAllLogs">
        <text class="bottom-icon">📋</text>
        <text class="bottom-text">全部操作记录</text>
      </view>
      <view class="bottom-divider"></view>
      <view class="bottom-btn" @click="showBatchAction">
        <text class="bottom-icon">⚙</text>
        <text class="bottom-text">批量操作资产</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import request from '@/utils/request'

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
  const status = uni.getStorageSync('active_asset_status')
  if (status !== undefined && status !== null) {
    activeTab.value = status
    loadData(true)
    // 延时或标记删除，确保只在跳转时触发一次
    uni.removeStorageSync('active_asset_status')
  }
})

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
    }
    if (keyword.value) params.keyword = keyword.value
    if (activeTab.value) params.status = activeTab.value

    const res = await request.get('/assets/', params)
    if (res && res.length > 0) {
      assetList.value.push(...res)
      skip.value += limit
      if (res.length < limit) hasMore.value = false
      // 简易统计（无精确 count 接口时用当前加载量估算）
      if (total.value === 0 || reset) total.value = res.length
      else total.value = assetList.value.length
    } else {
      hasMore.value = false
      if (reset) total.value = 0
    }
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '加载失败，请重试', icon: 'none', duration: 2000 })
  } finally {
    loading.value = false
  }
}

// 获取资产总数（异步更新）
const fetchTotal = async () => {
  try {
    const res = await request.get('/assets/', { skip: 0, limit: 9999 })
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
const showBatchAction = () => {
  uni.showActionSheet({
    itemList: ['批量标记"在用"', '批量标记"闲置"', '批量标记"维修"'],
    success: (res) => {
      const actions = ['在用', '闲置', '维修']
      uni.showToast({ title: `批量操作: ${actions[res.tapIndex]}`, icon: 'none' })
    }
  })
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
          font-size: 12px;
          color: #999;
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

/* ===== 底部操作栏 ===== */
.bottom-bar {
  display: flex;
  align-items: center;
  background: #fff;
  border-top: 1px solid #eee;
  padding: 10px 0;
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  
  .bottom-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    
    .bottom-icon {
      font-size: 16px;
    }
    .bottom-text {
      font-size: 13px;
      color: #555;
    }
  }
  
  .bottom-divider {
    width: 1px;
    height: 20px;
    background: #eee;
  }
}
</style>
