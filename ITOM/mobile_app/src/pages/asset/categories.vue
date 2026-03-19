<template>
  <view class="container">
    <scroll-view scroll-y class="list-container">
      <view class="category-card" v-for="item in categories" :key="item.id">
        <view class="card-header">
          <text class="name">{{ item.name }}</text>
          <text class="action-btn" @click="editCategory(item)">编辑属性</text>
        </view>
        <view class="card-body">
          <view class="attr-title">包含的扩展属性:</view>
          <view class="attr-tags">
            <text class="tag" v-for="(type, key) in item.default_attributes" :key="key">{{ key }} ({{ type }})</text>
            <text class="tag empty" v-if="Object.keys(item.default_attributes || {}).length === 0">暂无扩展属性</text>
          </view>
        </view>
      </view>
      
      <view class="empty-state" v-if="!loading && categories.length === 0">暂无分类数据</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const categories = ref<any[]>([])
const loading = ref(false)

const loadCategories = async () => {
  loading.value = true
  try {
    const res = await request.get('/assets/categories', { limit: 100 })
    categories.value = res || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const editCategory = (item: any) => {
  uni.showToast({ title: '移动端建议仅查询，修改请前往PC端', icon: 'none' })
}

onMounted(() => {
  loadCategories()
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding: 15px;
}

.category-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f5f5f5;
    padding-bottom: 10px;
    margin-bottom: 10px;
    
    .name {
      font-size: 16px;
      font-weight: bold;
      color: #333;
    }
    
    .action-btn {
      font-size: 13px;
      color: #007aff;
    }
  }
  
  .card-body {
    .attr-title {
      font-size: 13px;
      color: #888;
      margin-bottom: 8px;
    }
    
    .attr-tags {
      display: flex;
      flex-wrap: wrap;
      
      .tag {
        font-size: 12px;
        background: #f0f8ff;
        color: #007aff;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 8px;
        margin-bottom: 8px;
        
        &.empty {
          background: #f5f5f5;
          color: #999;
        }
      }
    }
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #999;
  font-size: 14px;
}
</style>
