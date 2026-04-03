<template>
  <view class="page-wrap">
    <view class="header-bar">
      <text class="header-title">资产盘点</text>
      <text class="header-sub">{{ checkedCount }}/{{ assetList.length }} 已确认</text>
    </view>

    <view class="progress-bar-wrap">
      <view class="progress-bar">
        <view class="progress-fill" :style="{ width: progressPct + '%' }"></view>
      </view>
      <text class="progress-label">{{ progressPct }}%</text>
    </view>

    <scroll-view scroll-y class="list-scroll">
      <view
        class="inv-card"
        v-for="item in assetList"
        :key="item.id"
        :class="{ checked: item._checked }"
      >
        <view class="inv-info">
          <text class="inv-code">{{ item.asset_code }}</text>
          <text class="inv-cat">{{ item.category?.name || '' }}</text>
          <text class="inv-owner" v-if="item.owner">使用人：{{ item.owner.name }}</text>
        </view>
        <view class="inv-action" @click="toggleCheck(item)">
          <view class="check-btn" :class="{ done: item._checked }">
            <text class="check-icon">{{ item._checked ? '✓' : '+' }}</text>
          </view>
          <text class="check-label">{{ item._checked ? '已盘点' : '确认盘点' }}</text>
        </view>
      </view>

      <view class="list-status" v-if="loading">
        <text>加载中...</text>
      </view>
      <view class="list-status" v-else-if="assetList.length === 0">
        <text>暂无资产数据</text>
      </view>
      <view style="height: 100rpx;"></view>
    </scroll-view>

    <view class="bottom-actions">
      <view class="submit-btn" @click="submitInventory">
        <text class="submit-text">提交本次盘点结果</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'

const assetList = ref<any[]>([])
const loading = ref(false)

const checkedCount = computed(() => assetList.value.filter(i => i._checked).length)
const progressPct = computed(() => {
  if (assetList.value.length === 0) return 0
  return Math.round((checkedCount.value / assetList.value.length) * 100)
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await request.get('/assets/', { limit: 200 })
    assetList.value = (res || []).map((item: any) => ({ ...item, _checked: false }))
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const toggleCheck = (item: any) => {
  item._checked = !item._checked
}

const submitInventory = () => {
  if (checkedCount.value === 0) {
    uni.showToast({ title: '请先确认至少一条资产', icon: 'none' })
    return
  }
  uni.showModal({
    title: '提交盘点',
    content: `本次共确认 ${checkedCount.value} 条资产，是否提交？`,
    success: (res) => {
      if (res.confirm) {
        uni.showToast({ title: '盘点结果已提交！', icon: 'success' })
        // 重置
        assetList.value.forEach(i => i._checked = false)
      }
    }
  })
}

onMounted(() => loadData())
</script>

<style lang="scss" scoped>
.page-wrap {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.header-bar {
  background: #1677ff;
  padding: 50px 16px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  
  .header-title {
    font-size: 20px;
    font-weight: 700;
    color: #fff;
  }
  .header-sub {
    font-size: 13px;
    color: rgba(255,255,255,0.8);
  }
}

.progress-bar-wrap {
  background: #fff;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  
  .progress-bar {
    flex: 1;
    height: 6px;
    background: #e8e8e8;
    border-radius: 3px;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: #1677ff;
      border-radius: 3px;
      transition: width 0.3s;
    }
  }
  
  .progress-label {
    font-size: 12px;
    color: #1677ff;
    font-weight: 600;
    width: 36px;
    text-align: right;
  }
}

.list-scroll {
  flex: 1;
  height: 0;
  padding: 10px 12px;
}

.inv-card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  border: 1.5px solid transparent;
  
  &.checked {
    border-color: #1677ff;
    background: #f0f6ff;
  }
  
  .inv-info {
    flex: 1;
    
    .inv-code { display: block; font-size: 15px; font-weight: 600; color: #1a1a1a; }
    .inv-cat  { display: block; font-size: 12px; color: #888; margin-top: 3px; }
    .inv-owner { display: block; font-size: 12px; color: #aaa; margin-top: 2px; }
  }
  
  .inv-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    .check-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #e8e8e8;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.done { background: #1677ff; }
      
      .check-icon { font-size: 18px; color: #fff; font-weight: bold; }
    }
    
    .check-label { font-size: 11px; color: #999; }
  }
}

.list-status {
  text-align: center;
  padding: 20px;
  color: #ccc;
  font-size: 13px;
}

.bottom-actions {
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid #eee;
  
  .submit-btn {
    background: #1677ff;
    height: 48px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .submit-text { font-size: 15px; color: #fff; font-weight: 600; }
  }
}
</style>
