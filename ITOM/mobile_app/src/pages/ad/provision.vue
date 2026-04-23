<template>
  <view class="container">
    <view class="card">
      <view class="form-title">开通 AD 域账户向导</view>
      
      <view class="form-item">
        <text class="label">用户工号*</text>
        <input class="input" v-model="form.new_username" placeholder="如 1001" />
      </view>
      
      <view class="form-item">
        <text class="label">姓名*</text>
        <input class="input" v-model="form.new_display_name" placeholder="如 张三" />
      </view>
      
      <view class="form-item">
        <text class="label">初始密码 (只读)*</text>
        <input class="input" password disabled v-model="form.password" placeholder="见权限模板配置" />
      </view>
      
      <view class="form-item">
        <text class="label">所属组织架构 (OU)*</text>
        <picker mode="selector" :range="ouOptions" range-key="name" @change="onOuChange">
          <view class="picker-value">{{ selectedOuName || '请选择 OU' }} ></view>
        </picker>
      </view>
      
      <button class="submit-btn" :loading="loading" @click="submit">一键极速开通</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const form = ref({
  new_username: '',
  new_display_name: '',
  password: '',
  ou_path: '',
  position_name: '',
  groups: []
})

const ouOptions = ref<any[]>([])
const selectedOuName = ref('')
const loading = ref(false)

const loadInitialData = async () => {
  try {
    const res = await request.get('/ad/ous')
    ouOptions.value = res || []
  } catch (e) {}

  try {
    const config = await request.get('/settings/config')
    if (config.DEFAULT_USER_PASSWORD) {
      form.value.password = config.DEFAULT_USER_PASSWORD
    }
  } catch (e) {}
}

const onOuChange = (e: any) => {
  const index = e.detail.value
  const ou = ouOptions.value[index]
  if (ou) {
    selectedOuName.value = ou.name
    form.value.ou_path = ou.dn
  }
}

const submit = async () => {
  if (!form.value.new_username || !form.value.new_display_name || !form.value.password || !form.value.ou_path) {
    uni.showToast({ title: '请填写完整带 * 必填项', icon: 'none' })
    return
  }
  
  loading.value = true
  try {
    uni.showLoading({ title: '入域交互中...' })
    const res = await request.post('/ad/users', form.value)
    uni.hideLoading()
    uni.showToast({ title: 'AD 账户开通成功!', icon: 'success' })
    // Reset identity fields only for continuous creation
    form.value.new_username = ''
    form.value.new_display_name = ''
    // Do NOT clear password and ou_path here for convenience
  } catch (e: any) {
    uni.hideLoading()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadInitialData()
})
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding: 20px;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  
  .form-title {
    font-size: 18px;
    font-weight: bold;
    color: #333;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    
    &::before {
      content: '';
      display: inline-block;
      width: 4px;
      height: 16px;
      background: #e51923;
      margin-right: 8px;
      border-radius: 2px;
    }
  }
  
  .form-item {
    margin-bottom: 20px;
    
    .label {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
      display: block;
    }
    
    .input {
      height: 44px;
      background: #f9f9f9;
      border-radius: 8px;
      padding: 0 12px;
      font-size: 15px;
      border: 1px solid transparent;
      
      &:focus {
        border-color: #e51923;
        background: #fff;
      }
    }
    
    .picker-value {
      height: 44px;
      line-height: 44px;
      background: #f9f9f9;
      border-radius: 8px;
      padding: 0 12px;
      font-size: 15px;
      color: #333;
    }
  }
  
  .submit-btn {
    margin-top: 30px;
    background: #e51923;
    color: #fff;
    border-radius: 8px;
    font-size: 16px;
    
    &::after { border: none; }
    &:active { background: #b91c1c; }
  }
}
</style>
