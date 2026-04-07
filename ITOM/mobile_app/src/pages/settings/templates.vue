<template>
  <view class="container">
    <view class="card">
      <view class="section-title">🔒 权限模板配置</view>
      <view class="desc">预设的岗位权限组。目前核心权限管控暂未对移动端开放读写操作。</view>
      
      <view class="template-item">
        <text class="title">默认管理员模板 (SuperAdmin)</text>
        <text class="content">包含系统完全控制权限，支持域账号创建与资产删除。</text>
      </view>
      
      <view class="template-item">
        <text class="title">基础运维模板 (Operator)</text>
        <text class="content">提供资产流转、域用户状态查看、密码重置权限。</text>
      </view>
      
      <view class="empty-state">
        新增与分配操作请前往 PC 端控制台
      </view>
    </view>
  </view>
</template>

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
  
  .template-item {
    background: #fdfdfd;
    border: 1px solid #eee;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 12px;
    
    .title {
      font-size: 15px;
      font-weight: bold;
      color: #007aff;
      margin-bottom: 8px;
      display: block;
    }
    
    .content {
      font-size: 13px;
      color: #666;
      display: block;
      margin-bottom: 4px;
    }
  }
}

.empty-state {
  text-align: center;
  padding: 20px 0;
  color: #999;
  font-size: 13px;
}
</style>
