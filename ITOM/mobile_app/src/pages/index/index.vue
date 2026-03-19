<template>
  <view class="container">
    <view class="header">
      <view class="title">ITOM 移动工作台</view>
    </view>
    
    <!-- 资产管理 -->
    <view class="section-group">
      <view class="group-title">资产管理</view>
      <view class="grid">
        <view class="grid-item" @click="navTo('/pages/asset/list')">
          <view class="icon bg-blue">💻</view>
          <text>资产台账</text>
        </view>
        <view class="grid-item" @click="navTo('/pages/asset/categories')">
          <view class="icon bg-blue">📑</view>
          <text>资产分类</text>
        </view>
      </view>
    </view>

    <!-- 身份凭据域 -->
    <view class="section-group">
      <view class="group-title">身份与凭据域 (AD)</view>
      <view class="grid">
        <view class="grid-item" @click="navTo('/pages/ad/users')">
          <view class="icon bg-green">👥</view>
          <text>域用户查询</text>
        </view>
        <view class="grid-item" @click="navTo('/pages/ad/provision')">
          <view class="icon bg-green">✨</view>
          <text>自动开通向导</text>
        </view>
        <view class="grid-item" @click="navTo('/pages/ad/groups')">
          <view class="icon bg-green">🛡️</view>
          <text>安全组策略</text>
        </view>
      </view>
    </view>

    <!-- 系统底座 -->
    <view class="section-group">
      <view class="group-title">系统底座</view>
      <view class="grid">
        <view class="grid-item" @click="navTo('/pages/settings/system')">
          <view class="icon bg-purple">⚙️</view>
          <text>全局配置</text>
        </view>
        <view class="grid-item" @click="navTo('/pages/settings/rules')">
          <view class="icon bg-purple">📝</view>
          <text>命名规范中心</text>
        </view>
        <view class="grid-item" @click="navTo('/pages/settings/templates')">
          <view class="icon bg-purple">🔑</view>
          <text>权限模板</text>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
const navTo = (url: string) => {
  uni.navigateTo({ url })
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding-bottom: 20px;
}

.header {
  background-color: #007aff;
  padding: 60px 20px 30px;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  margin-bottom: 10px;
  
  .title {
    color: #fff;
    font-size: 24px;
    font-weight: bold;
  }
}

.section-group {
  margin: 15px;
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  
  .group-title {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
    padding-left: 8px;
    border-left: 3px solid #007aff;
  }
}

.grid {
  display: flex;
  flex-wrap: wrap;
  
  .grid-item {
    width: 25%;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 15px;
    
    .icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      margin-bottom: 8px;
    }
    
    text {
      font-size: 12px;
      color: #333;
      text-align: center;
      line-height: 1.2;
    }
  }
}

.bg-blue { background-color: #e5f1ff; }
.bg-green { background-color: #e6f9ed; }
.bg-purple { background-color: #f3e5f5; }
</style>
