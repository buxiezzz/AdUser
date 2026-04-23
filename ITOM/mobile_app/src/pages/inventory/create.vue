<template>
  <view class="page-wrap">
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="back" @click="goBack">‹</view>
      <text class="title">新建盘点项目</text>
    </view>

    <view class="form-container">
      <view class="form-item">
        <text class="label">任务名称</text>
        <input class="input" v-model="form.name" placeholder="例如：2026年Q2季度定期盘点" />
      </view>

      <view class="form-item">
        <text class="label">任务描述 (可选)</text>
        <textarea class="textarea" v-model="form.description" placeholder="请输入本次盘点的备注信息..." />
      </view>

      <view class="scope-tip">
        <text class="tip-icon">ℹ️</text>
        <text class="tip-text">提示：新建任务后，系统会自动将当前所有在册资产导入盘点清单。</text>
      </view>

      <button class="submit-btn" :loading="submitting" @click="submitTask">创建并立即开始</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import request from '@/utils/request'

const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 20)
const submitting = ref(false)

const form = reactive({
  name: '',
  description: ''
})

const goBack = () => uni.navigateBack()

const submitTask = async () => {
  if (!form.name) {
    uni.showToast({ title: '请输入任务名称', icon: 'none' })
    return
  }
  
  submitting.value = true
  try {
    const res = await request.post('/inventory/tasks', {
      name: form.name,
      description: form.description
    })
    
    uni.showToast({ title: '创建成功', icon: 'success' })
    
    // 延迟跳转到执行页
    setTimeout(() => {
      uni.redirectTo({
        url: `/pages/inventory/execute?id=${res.id}&name=${encodeURIComponent(res.name)}`
      })
    }, 1500)
    
  } catch (e) {
    uni.showToast({ title: '创建失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #f7f9fc;
}
.header {
  background: #fff;
  padding-bottom: 12px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #efefef;
  position: relative;
  .back { width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; font-size: 30px; color: #333; }
  .title { flex: 1; text-align: center; font-size: 17px; font-weight: 600; margin-right: 44px; }
}

.form-container {
  padding: 20px;
}

.form-item {
  margin-bottom: 24px;
  .label { font-size: 14px; color: #666; font-weight: bold; margin-bottom: 10px; display: block; }
  .input { background: #fff; border-radius: 8px; padding: 12px 15px; font-size: 15px; border: 1px solid #e0e0e0; }
  .textarea { background: #fff; border-radius: 8px; padding: 12px 15px; font-size: 15px; border: 1px solid #e0e0e0; width: 100%; height: 120px; }
}

.scope-tip {
  background: #e6f7ff;
  padding: 12px;
  border-radius: 8px;
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  .tip-icon { font-size: 16px; }
  .tip-text { font-size: 13px; color: #1890ff; line-height: 1.5; }
}

.submit-btn {
  background: #e51923;
  color: #fff;
  border-radius: 25px;
  height: 50px;
  line-height: 50px;
  font-size: 16px;
  font-weight: bold;
  &::after { border: none; }
}
</style>
