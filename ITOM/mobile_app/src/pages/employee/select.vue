<template>
  <view class="page-wrap">
    <view class="search-wrap">
      <view class="search-bar">
        <input 
          class="search-input" 
          v-model="empKeyword" 
          @input="onSearchInput" 
          placeholder="🔍 输入姓名拼音、账号或部门找人" 
          focus
        />
        <text class="cancel-text" @click="cancelSelect">取消</text>
      </view>
    </view>

    <scroll-view scroll-y class="list-wrap">
      <view class="emp-list">
        <view class="emp-item clear-item" @click="selectEmployee(null)">
          <text>取消绑定 / 不选择使用人</text>
        </view>
        <view 
          class="emp-item" 
          v-for="emp in employees" 
          :key="emp.id" 
          @click="selectEmployee(emp)"
        >
           <view class="emp-info">
             <text class="emp-name">{{ emp.name }}</text>
             <text class="emp-dept">{{ emp.department || '此用户暂未关联组织部门' }}</text>
           </view>
           <text class="emp-account">{{ emp.ad_account || '本地' }}</text>
        </view>
        <view v-if="employees.length === 0" class="empty-tip">未找到匹配的人员</view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const employees = ref<any[]>([])
const empKeyword = ref('')
let searchTimer: any = null

const loadEmployees = async (keyword: string = '') => {
  try {
    const res = await request.get('/assets/employees', { keyword })
    employees.value = res || []
  } catch (e) {
    console.error('加载员工列表失败', e)
  }
}

const onSearchInput = (e: any) => {
  const val = e.detail.value
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadEmployees(val)
  }, 500)
}

const selectEmployee = (emp: any) => {
  uni.$emit('employee_selected', emp)
  uni.navigateBack()
}

const cancelSelect = () => {
  uni.navigateBack()
}

onMounted(() => {
  loadEmployees()
})
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.search-wrap {
  padding: 10px 15px;
  background: #fff;
  border-bottom: 1px solid #ebebeb;
}

.search-bar {
  display: flex;
  align-items: center;
  
  .search-input {
    flex: 1;
    background: #f0f2f5;
    border-radius: 18px;
    padding: 8px 16px;
    font-size: 14px;
    height: 36px;
  }
  
  .cancel-text {
    margin-left: 12px;
    font-size: 14px;
    color: #1677ff;
  }
}

.list-wrap {
  flex: 1;
  background: #fff;
}

.emp-list {
  width: 100%;
}

.emp-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f9f9f9;
  
  &:active {
    background: #f0f0f0;
  }
}

.clear-item {
  justify-content: center;
  color: #ff4d4f;
  font-size: 15px;
}

.emp-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
  
  .emp-name {
    font-size: 16px;
    font-weight: 500;
    color: #333;
  }
  
  .emp-dept {
    font-size: 12px;
    color: #888;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}

.emp-account {
  font-size: 12px;
  color: #1677ff;
  background: #e6f0ff;
  padding: 4px 8px;
  border-radius: 4px;
}

.empty-tip {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
}
</style>
