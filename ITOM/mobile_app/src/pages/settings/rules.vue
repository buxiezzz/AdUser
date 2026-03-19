<template>
  <view class="container">
    <view class="card">
      <view class="section-title">📝 命名规范字典中心</view>
      <view class="desc">为保证资产和域账户命名统一，此列表列出了组织内所有的命名约束与参考标准。</view>
      
      <view class="rule-item">
        <text class="title">主机名命名规范</text>
        <text class="content">规则: {{'['}}城市代号{{']'}}-{{'['}}部门代号{{']'}}-{{'['}}编号{{']'}}</text>
        <text class="content">示例: SH-DEV-001</text>
      </view>
      
      <view class="rule-item">
        <text class="title">AD 账号规范</text>
        <text class="content">规则: 名的拼音全拼 + 姓的拼音首字母</text>
        <text class="content">示例: 张三 -> san.z</text>
      </view>
      
      <view class="empty-state">
        规范细则目前由 PC 端控制台负责增减
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
  
  .rule-item {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 12px;
    
    .title {
      font-size: 15px;
      font-weight: bold;
      color: #333;
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
