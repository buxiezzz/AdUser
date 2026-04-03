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
          <view class="menu-item" @click="navTo('/pages/settings/rules')">
            <text class="menu-icon">📝</text>
            <text class="menu-label">命名规范中心</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/settings/templates')">
            <text class="menu-icon">🔑</text>
            <text class="menu-label">权限模板配置</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/asset/categories')">
            <text class="menu-icon">📑</text>
            <text class="menu-label">资产分类字典</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- AD 域管理 -->
      <view class="section">
        <view class="section-title">域管理（AD）</view>
        <view class="menu-group">
          <view class="menu-item" @click="navTo('/pages/ad/users')">
            <text class="menu-icon">👥</text>
            <text class="menu-label">域用户检索</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/ad/provision')">
            <text class="menu-icon">✨</text>
            <text class="menu-label">自动开通向导</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="navTo('/pages/ad/groups')">
            <text class="menu-icon">🛡️</text>
            <text class="menu-label">安全组策略</text>
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
        <view class="logout-btn" @click="logout">
          <text class="logout-text">退出登录</text>
        </view>
      </view>

      <view style="height: 30rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
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
  uni.showModal({
    title: '退出确认',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('token')
        uni.reLaunch({ url: '/pages/login/login' })
      }
    }
  })
}
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
    
    .logout-text { font-size: 15px; color: #ff4d4f; }
  }
}
</style>
