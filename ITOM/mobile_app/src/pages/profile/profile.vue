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
      <view class="menu-item" @click="showChangePwd = true">
        <text class="icon">🔒</text>
        <text class="title">修改登录密码</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item">
        <text class="icon">ℹ️</text>
        <text class="title">关于 ITOM 移动版</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item logout" @click="handleLogout">
        <text class="title">退出当前账号</text>
      </view>
    </view>

    <!-- 修改密码弹窗 -->
    <view v-if="showChangePwd" class="pwd-modal" @click.stop="">
      <view class="modal-content">
        <text class="modal-title">修改登录密码</text>
        <input v-model="oldPassword" password placeholder="请输入当前原密码" class="modal-input" />
        <input v-model="newPassword" password placeholder="设置新密码 (≥6位)" class="modal-input" />
        <view class="modal-btns">
          <button @click="showChangePwd = false" class="btn-cancel">取消</button>
          <button @click="submitChangePassword" class="btn-ok">确认修改</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import request from '../../utils/request'

const showChangePwd = ref(false)
const oldPassword = ref('')
const newPassword = ref('')

const submitChangePassword = async () => {
  if (!oldPassword.value || !newPassword.value) {
    return uni.showToast({ title: '请完整填写密码', icon: 'none' })
  }
  if (newPassword.value.length < 6) {
    return uni.showToast({ title: '新密码不能少于6位', icon: 'none' })
  }
  
  uni.showLoading({ title: '提交中...' })
  try {
    await request.post('/api/auth/change-password', {
      old_password: oldPassword.value,
      new_password: newPassword.value
    })
    uni.hideLoading()
    uni.showToast({ title: '修改成功，请重新登录', icon: 'success' })
    setTimeout(() => {
      uni.removeStorageSync('itom_token')
      uni.reLaunch({ url: '/pages/login/login' })
    }, 1500)
  } catch (e) {
    uni.hideLoading()
  }
}

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

.pwd-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  
  .modal-content {
    width: 80%;
    background-color: #fff;
    border-radius: 12px;
    padding: 24px;
    
    .modal-title {
      display: block;
      font-size: 18px;
      font-weight: bold;
      text-align: center;
      margin-bottom: 20px;
    }
    
    .modal-input {
      background-color: #f5f7f9;
      height: 44px;
      border-radius: 8px;
      margin-bottom: 12px;
      padding: 0 12px;
      font-size: 14px;
    }
    
    .modal-btns {
      display: flex;
      margin-top: 20px;
      gap: 12px;
      
      button {
        flex: 1;
        font-size: 15px;
        height: 40px;
        line-height: 40px;
        
        &.btn-cancel {
          background-color: #f0f0f0;
          color: #666;
        }
        
        &.btn-ok {
          background-color: #e51923;
          color: #fff;
        }
      }
    }
  }
}
</style>
