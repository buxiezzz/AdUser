<template>
  <view class="page-wrap">
    <view class="header">
      <text class="title">资产入库</text>
      <text class="subtitle">录入新设备信息到 ITOM 系统</text>
    </view>

    <scroll-view scroll-y class="scroll-body">
      <view class="form-container">
        <!-- 基本信息 -->
        <view class="form-section">
          <view class="section-title">基本信息</view>
          
          <view class="form-item required">
            <text class="label">资产编码</text>
            <input 
              class="input" 
              v-model="form.asset_code" 
              placeholder="必填，请输入资产/财务编码" 
            />
          </view>

          <view class="form-item required">
            <text class="label">资产分类</text>
            <picker 
              mode="selector" 
              :range="categories" 
              range-key="name" 
              @change="onCategoryChange"
            >
              <view class="picker-val" :class="{ placeholder: !selectedCategory }">
                {{ selectedCategory ? selectedCategory.name : '请选择分类' }}
                <text class="arrow">›</text>
              </view>
            </picker>
          </view>

          <view class="form-item">
            <text class="label">规格型号</text>
            <input class="input" v-model="form.dynamic_attributes['规格型号']" placeholder="如：ThinkPad X1" />
          </view>
          
          <view class="form-item">
            <text class="label">序列号(SN)</text>
            <input class="input" v-model="form.dynamic_attributes['序列号']" placeholder="请输入硬件SN码" />
          </view>
          
          <view class="form-item">
            <text class="label">计量单位</text>
            <input class="input" v-model="form.dynamic_attributes['计量单位']" placeholder="如：台 / 个 / 对" />
          </view>

          <view class="form-item">
            <text class="label">当前状态</text>
            <picker 
              mode="selector" 
              :range="statusOptions" 
              @change="onStatusChange"
            >
              <view class="picker-val">
                {{ form.status }}
                <text class="arrow">›</text>
              </view>
            </picker>
          </view>

          <view class="form-item" @click="openReassign">
            <text class="label">使用人 / 管理人</text>
            <view class="picker-val" :class="{ placeholder: !selectedEmployee }">
              {{ selectedEmployee ? selectedEmployee.name : '搜素姓名或账号(点击选择)' }}
              <text class="arrow">›</text>
            </view>
          </view>
          
          <view class="form-item">
            <text class="label">使用日期</text>
            <picker mode="date" :value="form.dynamic_attributes['使用日期']" @change="onDateChange">
              <view class="picker-val">
                {{ form.dynamic_attributes['使用日期'] }}
                <text class="arrow">›</text>
              </view>
            </picker>
          </view>
        </view>

        <!-- 详细属性 (动态加载) -->
        <view class="form-section" v-if="dynamicAttrFields.filter(f => !['规格型号','序列号','计量单位','使用日期'].includes(f)).length > 0">
          <view class="section-title">详细属性 ({{ selectedCategory?.name }})</view>
          
          <template v-for="field in dynamicAttrFields" :key="field">
            <view class="form-item" v-if="!['规格型号','序列号','计量单位','使用日期'].includes(field)">
              <text class="label">{{ field }}</text>
              <input 
                class="input" 
                v-model="form.dynamic_attributes[field]" 
                :placeholder="'请输入' + field" 
              />
            </view>
          </template>
        </view>
      </view>

      <view class="footer-tips">
        <text>提示：入库成功后将自动生成资产详情及二维码</text>
      </view>
      
      <view style="height: 100rpx;"></view>
    </scroll-view>

    <view class="bottom-bar">
      <view class="submit-btn" :class="{ loading: submitting }" @click="submitForm">
        <text class="btn-text">{{ submitting ? '正在提交...' : '确认入库' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import request from '@/utils/request'

interface Category {
  id: number
  name: string
  default_attributes: Record<string, any>
}

interface Employee {
  id: number
  name: string
  department?: string
  ad_account?: string
}

const categories = ref<Category[]>([])
const employees = ref<Employee[]>([])
const statusOptions = ['闲置', '在用', '维修', '报废', '下账']

const selectedCategory = ref<Category | null>(null)
const selectedEmployee = ref<Employee | null>(null)
const dynamicAttrFields = ref<string[]>([])

const form = reactive({
  asset_code: '',
  category_id: 0,
  status: '闲置',
  owner_id: null as number | null,
  dynamic_attributes: {
    '规格型号': '',
    '序列号': '',
    '计量单位': '台',
    '使用日期': new Date().toISOString().split('T')[0]
  } as Record<string, any>
})

const onDateChange = (e: any) => {
  form.dynamic_attributes['使用日期'] = e.detail.value
}

const submitting = ref(false)

const loadInitialData = async () => {
  try {
    const catRes = await request.get('/assets/categories')
    categories.value = catRes || []
  } catch (e) {
    console.error('Failed to load categories', e)
  }
}

const openReassign = () => {
  if (form.status === '报废' || form.status === '下账') {
    uni.showToast({ title: `该状态下不可绑定使用人`, icon: 'none' })
    return
  }
  // 方案 A：允许闲置状态下选人，选完会联动变状态
  uni.navigateTo({ url: '/pages/employee/select' })
}

const confirmReassign = (emp: any) => {
  if (!emp) {
    selectedEmployee.value = null
    form.owner_id = null
    if (form.dynamic_attributes) {
      form.dynamic_attributes['所属组织'] = ''
    }
  } else {
    selectedEmployee.value = emp
    form.owner_id = emp.id
    
    // 联动逻辑：如果当前是闲置，选了人自动变在用
    if (form.status === '闲置') {
      form.status = '在用'
    }
    
    if (form.dynamic_attributes) {
      form.dynamic_attributes['所属组织'] = emp.department || ''
    }
  }
}

const onCategoryChange = (e: any) => {
  const index = e.detail.value
  const cat = categories.value[index]
  selectedCategory.value = cat
  form.category_id = cat.id
  
  // 处理动态属性字段
  const attrs = cat.default_attributes || {}
  dynamicAttrFields.value = Object.keys(attrs)
  
  // 初始化动态属性值
  form.dynamic_attributes = {}
  dynamicAttrFields.value.forEach(key => {
    form.dynamic_attributes[key] = attrs[key] || ''
  })
}

const onStatusChange = (e: any) => {
  const newStatus = statusOptions[e.detail.value]
  form.status = newStatus
  
  // 业务逻辑：如果变成闲置或报废或下账，必须清空使用人
  if (newStatus === '闲置' || newStatus === '报废' || newStatus === '下账') {
    if (selectedEmployee.value) {
      selectedEmployee.value = null
      form.owner_id = null
      if (form.dynamic_attributes) {
        form.dynamic_attributes['所属组织'] = ''
      }
      uni.showToast({ title: '已根据状态自动解除使用人绑定', icon: 'none' })
    }
  }
}

const submitForm = async () => {
  if (submitting.value) return
  
  if (!form.asset_code || !form.asset_code.trim()) {
    uni.showToast({ title: '请输入资产编码', icon: 'none' })
    return
  }
  
  if (!form.category_id) {
    uni.showToast({ title: '请选择资产分类', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const res = await request.post('/assets/', form)
    uni.showToast({ title: '入库成功！', icon: 'success' })
    
    // 跳转到刚才创建的资产详情
    setTimeout(() => {
      uni.redirectTo({
        url: `/pages/asset/detail?id=${res.id}`
      })
    }, 1500)
  } catch (e) {
    // 错误已由 request 拦截提示
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadInitialData()
  uni.$on('employee_selected', confirmReassign)
})

// 组件销毁时移除监听
import { onUnmounted } from 'vue'
onUnmounted(() => {
  uni.$off('employee_selected', confirmReassign)
})
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.header {
  background: #fff;
  padding: 50px 20px 20px;
  border-bottom: 1px solid #eee;
  
  .title {
    font-size: 24px;
    font-weight: 700;
    color: #1a1a1a;
    display: block;
  }
  .subtitle {
    font-size: 13px;
    color: #999;
    margin-top: 4px;
    display: block;
  }
}

.scroll-body {
  flex: 1;
}

.form-container {
  padding: 16px;
}

.form-section {
  background: #fff;
  border-radius: 12px;
  padding: 0 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #1677ff;
    padding: 14px 0 10px;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 4px;
  }
}

.form-item {
  min-height: 90rpx;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f8f8f8;
  padding: 10px 0;
  
  &:last-child { border-bottom: none; }
  
  &.required .label::after {
    content: '*';
    color: #ff4d4f;
    margin-left: 4px;
  }

  .label {
    width: 220rpx;
    font-size: 15px;
    color: #333;
  }
  
  .input {
    flex: 1;
    font-size: 15px;
    text-align: right;
  }
  
  .picker-val {
    flex: 1;
    font-size: 15px;
    color: #1a1a1a;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    width: 460rpx;
    text-align: right;
    
    &.placeholder { color: #ccc; }
    
    .arrow {
      color: #ccc;
      font-size: 20px;
      margin-left: 6px;
    }
  }
}

.footer-tips {
  padding: 0 20px;
  text-align: center;
  font-size: 12px;
  color: #999;
}

.bottom-bar {
  padding: 12px 20px calc(12px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid #eee;
  
  .submit-btn {
    height: 48px;
    background: #1677ff;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.3s;
    
    &.loading { opacity: 0.7; }
    
    .btn-text {
      color: #fff;
      font-size: 16px;
      font-weight: 600;
    }
  }
}
</style>
