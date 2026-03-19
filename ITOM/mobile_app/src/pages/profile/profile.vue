<template>
  <view class="container">
    <view class="header">
      <view class="avatar-box">
        <view class="avatar">👨‍💻</view>
        <view class="info">
          <text class="name">管理员</text>
          <text class="role">系统管理员</text>
        </view>
      </view>
    </view>
    
    <view class="menu-list">
      <view class="menu-item">
        <text class="icon">🔒</text>
        <text class="title">修改密码</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item">
        <text class="icon">ℹ️</text>
        <text class="title">关于 ITOM</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item logout" @click="handleLogout">
        <text class="title">退出登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('itom_token')
        uni.reLaunch({ url: '/pages/login/login' })
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
}

.header {
  background-color: #fff;
  padding: 40px 20px 30px;
  margin-bottom: 16px;
  
  .avatar-box {
    display: flex;
    align-items: center;
    
    .avatar {
      width: 64px;
      height: 64px;
      border-radius: 32px;
      background-color: #f0f0f0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      margin-right: 16px;
    }
    
    .info {
      display: flex;
      flex-direction: column;
      
      .name {
        font-size: 20px;
        font-weight: bold;
        color: #333;
        margin-bottom: 4px;
      }
      
      .role {
        font-size: 14px;
        color: #666;
      }
    }
  }
}

.menu-list {
  background-color: #fff;
  
  .menu-item {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #f5f5f5;
    
    .icon {
      font-size: 20px;
      margin-right: 12px;
    }
    
    .title {
      flex: 1;
      font-size: 16px;
      color: #333;
    }
    
    .arrow {
      color: #ccc;
      font-size: 16px;
    }
    
    &.logout {
      justify-content: center;
      border-bottom: none;
      
      .title {
        flex: none;
        color: #ff3b30;
        font-weight: 500;
      }
    }
  }
}
</style>
