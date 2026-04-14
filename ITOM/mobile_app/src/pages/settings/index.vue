<template>
  <view class="page-wrap">
    <view class="header">
      <text class="header-title">设置</text>
    </view>

    <scroll-view scroll-y class="scroll-body">
      <!-- 账号信息 -->
      <view class="section">
        <view class="section-title">账号</view>
        <view class="menu-group">
          <view class="menu-item" @click="goProfile">
            <text class="menu-icon">👤</text>
            <text class="menu-label">个人信息</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="changePassword">
            <text class="menu-icon">🔐</text>
            <text class="menu-label">修改密码</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 系统管理 -->
      <view class="section">
        <view class="section-title">系统管理</view>
        <view class="menu-group">
          <view class="menu-item" @click="navTo('/pages/settings/system')">
            <text class="menu-icon">⚙️</text>
            <text class="menu-label">全局配置</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/asset/categories')">
            <text class="menu-icon">📑</text>
            <text class="menu-label">资产分类字典</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 域账号创建 -->
      <view class="section">
        <view class="section-title">域账号创建</view>
        <view class="menu-group">
          <view class="menu-item" @click="navTo('/pages/ad/provision')">
            <text class="menu-icon">✨</text>
            <text class="menu-label">一键创建域账号</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/ad/users')">
            <text class="menu-icon">👥</text>
            <text class="menu-label">域用户检索</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/ad/groups')">
            <text class="menu-icon">🛡️</text>
            <text class="menu-label">安全策略组台账</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/settings/templates')">
            <text class="menu-icon">🔑</text>
            <text class="menu-label">权限模板配置</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/ad/filter')">
            <text class="menu-icon">🗺️</text>
            <text class="menu-label">地区过滤器</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 关于 -->
      <view class="section">
        <view class="menu-group">
          <view class="menu-item" @click="showAbout">
            <text class="menu-icon">ℹ️</text>
            <text class="menu-label">关于 ITOM</text>
            <text class="menu-value">v1.0.0</text>
          </view>
        </view>
      </view>

      <!-- 退出登录 -->
      <view class="logout-wrap">
        <view class="logout-btn" hover-class="btn-hover" @tap="logout" style="margin-bottom: 12px;">
          <text class="logout-text">退出当前账号</text>
        </view>
        <view class="logout-btn secondary" hover-class="btn-hover" @tap="exitApp" v-if="isNative">
          <text class="logout-text gray">彻底退出 APP 程序</text>
        </view>
      </view>

      <!-- 底部留白，防止被 TabBar 遮挡 -->
      <view style="height: 180rpx;"></view>
    </scroll-view>
    <CustomTabBar :activeIndex="4" />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import CustomTabBar from '@/components/CustomTabBar.vue'

const isNative = ref(false)
// #ifdef APP-PLUS
isNative.value = true
// #endif

const navTo = (url: string) => uni.navigateTo({ url })

const goProfile = () => navTo('/pages/profile/profile')

const changePassword = () => {
  uni.showToast({ title: '请前往PC端修改密码', icon: 'none', duration: 2000 })
}

const showAbout = () => {
  uni.showModal({
    title: 'ITOM 移动端',
    content: 'IT 资产运营管理平台 v1.0.0\nPowered by FastAPI + Uni-app',
    showCancel: false
  })
}

const logout = () => {
  console.log('触发退出登录')
  uni.vibrateShort({})
  uni.showModal({
    title: '退出确认',
    content: '确定要退出登录并返回登录页吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('itom_token')
        uni.reLaunch({ url: '/pages/login/login' })
      }
    }
  })
}

const exitApp = () => {
  console.log('触发退出程序')
  uni.vibrateShort({})
  uni.showModal({
    title: '彻底退出',
    content: '确定要关闭并退出 ITOM 程序吗？',
    success: (res) => {
      if (res.confirm) {
        // #ifdef APP-PLUS
        plus.runtime.quit();
        // #endif
        // #ifndef APP-PLUS
        uni.showToast({ title: '仅原生 App 支持彻底退出', icon: 'none' })
        // #endif
      }
    }
  })
}

onShow(() => {
  uni.hideTabBar()
})
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  background: #fff;
  padding: 50px 16px 14px;
  border-bottom: 1px solid #f0f0f0;
  
  .header-title {
    font-size: 20px;
    font-weight: 700;
    color: #1a1a1a;
  }
}

.scroll-body {
  padding-top: 4px;
}

.section {
  margin: 12px 0 0;
  
  .section-title {
    font-size: 12px;
    color: #999;
    padding: 0 16px 6px;
  }
  
  .menu-group {
    background: #fff;
    
    .menu-item {
      display: flex;
      align-items: center;
      padding: 14px 16px;
      border-bottom: 1px solid #f8f8f8;
      
      &:last-child { border-bottom: none; }
      
      .menu-icon { font-size: 18px; width: 28px; }
      .menu-label { flex: 1; font-size: 15px; color: #1a1a1a; }
      .menu-arrow { font-size: 18px; color: #ccc; }
      .menu-value { font-size: 13px; color: #999; }
    }
  }
}

.logout-wrap {
  padding: 20px 16px;
  
  .logout-btn {
    background: #fff;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #ff4d4f;
    
    &.secondary {
      border-color: #d9d9d9;
    }

    &.btn-hover {
      opacity: 0.6;
      background-color: #f0f0f0;
    }
    
    .logout-text { 
      font-size: 15px; 
      color: #ff4d4f; 
      
      &.gray { color: #888; }
    }
  }
}
</style>
