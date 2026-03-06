<template>
  <div class="min-h-screen bg-gray-100 font-sans text-gray-800 pb-20">
    <!-- Header -->
    <div class="bg-gradient-to-r from-blue-600 to-blue-500 text-white p-4 shadow-md sticky top-0 z-50 flex items-center">
      <el-icon class="mr-3 text-xl cursor-pointer" @click="goBack"><ArrowLeft /></el-icon>
      <h1 class="text-lg font-bold">新资产入库</h1>
    </div>

    <!-- Auth Guard -->
    <div v-if="!isAuthenticated" class="p-8 text-center mt-20">
      <el-icon class="text-5xl text-gray-300 mb-4"><Lock /></el-icon>
      <p class="text-gray-500 mb-6">您需要管理员权限才能录入新资产</p>
      <el-button type="primary" round class="w-full max-w-xs" @click="$router.push('/login')">去登录</el-button>
    </div>

    <!-- Create Form -->
    <div v-else class="p-4 pt-6 space-y-6">
      
      <!-- Basic Info Section -->
      <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <h2 class="text-sm font-bold text-blue-600 mb-4 flex items-center"><el-icon class="mr-2"><InfoFilled /></el-icon> 基础信息</h2>
        
        <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
          <el-form-item label="资产分类" prop="category_id">
            <el-select v-model="form.category_id" placeholder="请选择资产分类" class="w-full" size="large">
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="自定义资产编号" prop="asset_code">
            <el-input v-model="form.asset_code" placeholder="留空则系统自动生成" size="large"></el-input>
          </el-form-item>
          
          <el-form-item label="初始使用人" prop="owner_id">
            <el-select
              v-model="form.owner_id"
              filterable remote reserve-keyword clearable
              placeholder="搜索领用人 (留空即为库房闲置)"
              :remote-method="searchEmployees"
              :loading="employeeLoading"
              size="large" class="w-full"
            >
              <el-option v-for="emp in employees" :key="emp.id" :label="`${emp.name} (${emp.department})`" :value="emp.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- Hardware Specifics -->
      <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <h2 class="text-sm font-bold text-amber-500 mb-4 flex items-center"><el-icon class="mr-2"><Platform /></el-icon> 硬件规格</h2>
        <div class="space-y-4">
           <div>
             <label class="text-xs text-gray-500 mb-1 block">品牌/规格型号</label>
             <el-input v-model="dynamics['规格型号']" placeholder="例如: 联想ThinkPad T14" size="large"></el-input>
           </div>
           <div>
             <label class="text-xs text-gray-500 mb-1 block">硬件序列号 (SN)</label>
             <el-input v-model="dynamics['序列号']" placeholder="底部的 S/N 码" size="large"></el-input>
           </div>
        </div>
      </div>

    </div>

    <!-- Fixed Bottom Bar -->
    <div v-if="isAuthenticated" class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-100 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] flex gap-3 z-40">
      <el-button class="flex-1 !h-12 !rounded-xl text-base" @click="resetForm">重置</el-button>
      <el-button class="flex-[2] !h-12 !rounded-xl text-base font-bold shadow-md" type="primary" :loading="submitting" @click="submitAsset">
        <el-icon class="mr-2"><Check /></el-icon> 确认入库
      </el-button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ArrowLeft, Lock, Check, InfoFilled, Platform } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Setup Axios Interceptor for this view
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('itom_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

const router = useRouter()
const isAuthenticated = ref(!!localStorage.getItem('itom_token'))

const formRef = ref()
const submitting = ref(false)

const categories = ref<any[]>([])
const employees = ref<any[]>([])
const employeeLoading = ref(false)

const form = reactive({
    asset_code: '',
    category_id: null,
    owner_id: null,
    status: '在用'
})

// Specific standard attributes mapped from the dynamic attributes field
const dynamics = reactive<Record<string, string>>({
    '规格型号': '',
    '序列号': ''
})

const rules = {
    category_id: [{ required: true, message: '必须选择一个分类', trigger: 'change' }]
}

onMounted(() => {
    if (isAuthenticated.value) {
        fetchCategories()
    }
})

const goBack = () => router.back()

const fetchCategories = async () => {
    try {
        const res = await axios.get('/api/assets/categories')
        categories.value = res.data
    } catch (err) {
        ElMessage.error('无法加载资产分类')
    }
}

const searchEmployees = async (query: string) => {
    if (query) {
        employeeLoading.value = true
        try {
            const res = await axios.get('/api/assets/employees', { params: { keyword: query } })
            employees.value = res.data
        } catch (err) {
            console.error(err)
        } finally {
            employeeLoading.value = false
        }
    } else {
        employees.value = []
    }
}

const resetForm = () => {
    if (formRef.value) formRef.value.resetFields()
    dynamics['规格型号'] = ''
    dynamics['序列号'] = ''
}

const submitAsset = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
        if (!valid) return
        
        submitting.value = true
        try {
            // Re-map the form status based on if there's an owner
            const payload = {
                asset_code: form.asset_code || undefined,
                category_id: form.category_id,
                owner_id: form.owner_id,
                status: form.owner_id ? '在用' : '闲置',
                dynamic_attributes: {
                    '规格型号': dynamics['规格型号'],
                    '序列号': dynamics['序列号']
                }
            }
            
            const res = await axios.post('/api/assets/', payload)
            
            ElMessageBox.confirm(
                '资产已成功入库。是否立刻查看并打印标签？',
                '入库成功',
                {
                    confirmButtonText: '查看',
                    cancelButtonText: '继续录入',
                    type: 'success',
                    center: true
                }
            ).then(() => {
                router.replace(`/mobile/asset/${res.data.qr_code_token}`)
            }).catch(() => {
                resetForm()
            })
            
        } catch (err: any) {
            ElMessage.error(err.response?.data?.detail || '保存失败')
        } finally {
            submitting.value = false
        }
    })
}
</script>
