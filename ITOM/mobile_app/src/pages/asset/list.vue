<template>
  <view class="container">
    <view class="search-bar">
      <input class="search-input" v-model="keyword" placeholder="搜索资产名称、编码或使用者" @confirm="onSearch" />
      <view class="search-btn" @click="onSearch">搜索</view>
    </view>
    
    <scroll-view scroll-y class="list-container" @scrolltolower="loadMore">
      <view class="asset-card" v-for="item in assetList" :key="item.id" @click="goToDetail(item.id)">
        <view class="card-header">
          <text class="asset-code">{{ item.asset_code }}</text>
          <text :class="['status-tag', statusClass(item.status)]">{{ item.status }}</text>
        </view>
        <view class="card-body">
          <view class="info-row">
            <text class="label">资产分类:</text>
            <text class="value">{{ item.category?.name || '未知' }}</text>
          </view>
          <view class="info-row" v-if="item.owner">
            <text class="label">使用者:</text>
            <text class="value">{{ item.owner.name }} ({{ item.owner.department }})</text>
          </view>
          <view class="info-row" v-for="(v, k) in getPreviewAttributes(item.dynamic_attributes)" :key="k">
            <text class="label">{{ k }}:</text>
            <text class="value">{{ v }}</text>
          </view>
        </view>
      </view>
      
      <view class="loading-state" v-if="loading">加载中...</view>
      <view class="empty-state" v-if="!loading && assetList.length === 0">未找到资产数据</view>
      <view class="no-more" v-if="!loading && !hasMore && assetList.length > 0">没有更多了</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const keyword = ref('')
const assetList = ref<any[]>([])
const loading = ref(false)
const hasMore = ref(true)
const skip = ref(0)
const limit = 20

const loadData = async (reset = false) => {
  if (reset) {
    skip.value = 0
    assetList.value = []
    hasMore.value = true
  }
  
  if (!hasMore.value || loading.value) return
  
  loading.value = true
  try {
    const res = await request.get('/assets/', { skip: skip.value, limit })
    if (res && res.length > 0) {
      if (keyword.value) {
         // 前端简单过滤匹配
         const kw = keyword.value.toLowerCase()
         const filtered = res.filter((item: any) => 
            item.asset_code?.toLowerCase().includes(kw) ||
            item.owner?.name?.toLowerCase().includes(kw) ||
            item.category?.name?.toLowerCase().includes(kw)
         )
         assetList.value.push(...filtered)
      } else {
         assetList.value.push(...res)
      }
      skip.value += limit
      if (res.length < limit) hasMore.value = false
    } else {
      hasMore.value = false
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  loadData(true)
}

const loadMore = () => {
  loadData()
}

const goToDetail = (id: string) => {
  uni.navigateTo({ url: `/pages/asset/detail?id=${id}` })
}

const statusClass = (status: string) => {
  if (status === '在用') return 'status-active'
  if (status === '在库') return 'status-idle'
  if (status === '归档' || status === '报废') return 'status-offline'
  return 'status-default'
}

const getPreviewAttributes = (attrs: any) => {
  if (!attrs) return {}
  const keys = Object.keys(attrs).slice(0, 2)
  const res: any = {}
  keys.forEach(k => {
    res[k] = attrs[k]
  })
  return res
}

onMounted(() => {
  loadData(true)
})
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
    color: #007aff;
    font-size: 15px;
    padding: 5px;
  }
}

.list-container {
  flex: 1;
  padding: 10px 15px;
  
  .asset-card {
    background: #fff;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid #f5f5f5;
      
      .asset-code {
        font-size: 16px;
        font-weight: bold;
        color: #333;
      }
      
      .status-tag {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 10px;
        
        &.status-active { background: #e6f9ed; color: #00a854; }
        &.status-idle { background: #e5f1ff; color: #007aff; }
        &.status-offline { background: #f5f5f5; color: #999; }
        &.status-default { background: #fff2e5; color: #ff8c00; }
      }
    }
    
    .card-body {
      .info-row {
        display: flex;
        margin-bottom: 6px;
        font-size: 13px;
        
        .label {
          color: #999;
          width: 70px;
        }
        
        .value {
          color: #333;
          flex: 1;
        }
      }
    }
  }
}

.loading-state, .empty-state, .no-more {
  text-align: center;
  padding: 20px 0;
  color: #999;
  font-size: 13px;
}
</style>
