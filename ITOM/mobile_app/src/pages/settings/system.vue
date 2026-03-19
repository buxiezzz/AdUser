<template>
  <view class="container">
    <view class="card">
      <view class="section-title">ITOM 平台全局配置</view>
      <view class="desc">对 AD 域连接和基础设置进行配对。出于安全考量，密码类字段在移动端已遮蔽。</view>
      
      <view class="config-item" v-for="(v, k) in configData" :key="k">
        <text class="label">{{ k }}</text>
        <view class="value-box">
          <text class="value" v-if="k.includes('PASSWORD')">********</text>
          <text class="value" v-else>{{ v }}</text>
        </view>
      </view>
      
      <button class="edit-btn" @click="editConfig">修改全局配置</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const configData = ref<any>({})

const loadConfig = async () => {
  try {
    const res = await request.get('/settings/config')
    configData.value = res || {}
  } catch (e) {
    console.error(e)
  }
}

const editConfig = () => {
  uni.showToast({ title: '核心系统配置请移步至 PC 大屏浏览器操作', icon: 'none' })
}

onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding: 15px;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  
  .section-title {
    font-size: 18px;
    font-weight: bold;
    color: #333;
    margin-bottom: 8px;
  }
  
  .desc {
    font-size: 13px;
    color: #888;
    margin-bottom: 24px;
    line-height: 1.5;
  }
  
  .config-item {
    margin-bottom: 16px;
    border-bottom: 1px solid #f9f9f9;
    padding-bottom: 10px;
    
    .label {
      font-size: 14px;
      color: #666;
      margin-bottom: 6px;
      display: block;
    }
    
    .value-box {
      .value {
        font-size: 15px;
        color: #333;
        word-break: break-all;
      }
    }
  }
  
  .edit-btn {
    margin-top: 30px;
    background: #007aff;
    color: #fff;
    border-radius: 8px;
    font-size: 16px;
    
    &::after { border: none; }
    &:active { background: #0062cc; }
  }
}
</style>
