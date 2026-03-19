<template>
  <view class="login-container">
    <view class="logo-box">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="app-name">ITOM 移动端</text>
    </view>
    
    <view class="form-box">
      <view class="input-group">
        <text class="label">用户名</text>
        <input class="input" v-model="form.username" placeholder="请输入管理员账号" />
      </view>
      
      <view class="input-group">
        <text class="label">密码</text>
        <input class="input" password v-model="form.password" placeholder="请输入密码" />
      </view>
      
      <button class="login-btn" :loading="loading" @click="handleLogin">登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import request from '@/utils/request'

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
    return
  }
  
  loading.value = true
  try {
    const res = await uni.request({
      url: 'http://127.0.0.1:18000/api/auth/login', // 后续将整合 config
      method: 'POST',
      header: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      data: {
        username: form.username,
        password: form.password
      }
    })
    
    const data = res.data as any
    if (data && data.access_token) {
      uni.setStorageSync('itom_token', data.access_token)
      uni.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 1000)
    } else {
      uni.showToast({ title: data.detail || '登录失败', icon: 'none' })
    }
  } catch (err) {
    console.error('Login failed', err)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  padding: 40px 30px;
  min-height: 100vh;
  background-color: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.logo-box {
  margin-top: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60px;
  
  .logo {
    width: 80px;
    height: 80px;
    margin-bottom: 16px;
    background-color: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }
  
  .app-name {
    font-size: 24px;
    font-weight: bold;
    color: #333;
  }
}

.form-box {
  background: #fff;
  padding: 30px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  
  .input-group {
    margin-bottom: 24px;
    
    .label {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
      display: block;
    }
    
    .input {
      height: 44px;
      border-bottom: 1px solid #eee;
      font-size: 16px;
      padding: 0 8px;
      transition: all 0.3s;
      
      &:focus {
        border-bottom-color: #007aff;
      }
    }
  }
  
  .login-btn {
    margin-top: 40px;
    background-color: #007aff;
    color: #fff;
    border-radius: 8px;
    font-size: 16px;
    
    &::after {
      border: none;
    }
    
    &:active {
      background-color: #0062cc;
    }
  }
}
</style>
