<template>
  <div 
    class="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-cover bg-center bg-no-repeat"
    :style="{ backgroundImage: `url(${loginBg})` }"
  >
    
    <div class="sm:mx-auto sm:w-full sm:max-w-md mt-[-5%] mb-4 text-center">
      <div class="inline-flex items-center justify-center p-8 bg-white rounded-3xl shadow-xl border border-gray-100 mb-8">
        <img :src="logo" alt="Logo" class="h-24 w-auto" />
      </div>
      <h2 class="text-center text-3xl font-extrabold text-gray-900 tracking-tight">
        ITOM 运维中枢平台
      </h2>
      <p class="mt-2 text-center text-sm text-gray-500 font-medium">
        登录以访问资产与统一身份管理基座
      </p>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white/60 backdrop-blur-2xl py-10 px-4 shadow-2xl border border-white/80 sm:rounded-3xl sm:px-10">
        
        <!-- Toggle Login/Register -->
        <div class="flex border-b border-gray-200 mb-8" v-if="allowRegistration">
          <button 
            @click="isLoginMode = true"
            :class="['flex-1 pb-4 text-sm font-bold transition-colors', isLoginMode ? 'text-red-600 border-b-2 border-red-600' : 'text-gray-400 hover:text-gray-700']"
          >
            系统登入
          </button>
          <button 
            @click="isLoginMode = false"
            :class="['flex-1 pb-4 text-sm font-bold transition-colors', !isLoginMode ? 'text-red-600 border-b-2 border-red-600' : 'text-gray-400 hover:text-gray-700']"
          >
            注册管理员
          </button>
        </div>

        <el-form 
          ref="formRef" 
          :model="form" 
          :rules="rules" 
          label-position="top"
          @keyup.enter="handleSubmit"
        >
          <el-form-item label="管理员账号" prop="username">
            <el-input 
              v-model="form.username" 
              placeholder="请输入系统账号" 
              size="large"
              :prefix-icon="User"
              class="glass-input"
            />
          </el-form-item>

          <el-form-item label="身份凭证" prop="password">
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="请输入登录密码" 
              size="large"
              show-password
              :prefix-icon="Lock"
              class="glass-input"
            />
          </el-form-item>
          
          <el-form-item v-if="!isLoginMode" label="角色授权" prop="role">
            <el-select v-model="form.role" placeholder="请选择您的角色" size="large" class="w-full">
              <el-option label="系统管理员 (Admin)" value="admin" />
              <el-option label="普通维护者 (Operator)" value="operator" />
            </el-select>
          </el-form-item>

          <div class="flex items-center justify-between mb-6" v-if="isLoginMode">
            <div class="flex items-center">
              <el-checkbox v-model="rememberMe" label="记住我" size="small" />
            </div>
            <div class="text-sm">
              <a href="#" class="font-bold text-red-600 hover:text-red-700">
                忘记密码?
              </a>
            </div>
          </div>

          <el-button 
            type="primary" 
            class="w-full font-medium" 
            size="large"
            :loading="loading"
            @click="handleSubmit"
            style="background: linear-gradient(135deg, #e51923 0%, #b91c1c 100%); border: none;"
          >
            {{ isLoginMode ? '验证并登入' : '提交注册' }}
          </el-button>
        </el-form>
        
      </div>
    </div>
  </div>
</template>

<style scoped>
.glass-input :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.5) !important;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.05) inset !important;
  backdrop-filter: blur(5px);
}
.glass-input :deep(.el-input__inner) {
  color: #1a1a1a !important;
}
.glass-input :deep(.el-input__inner::placeholder) {
  color: #9ca3af !important;
}
:deep(.el-form-item__label) {
  color: #374151 !important;
  font-weight: 600;
}
:deep(.el-checkbox__label) {
  color: #4b5563 !important;
}
:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #e51923 !important;
  border-color: #e51923 !important;
}
</style>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import axios from 'axios'
import logo from '@/assets/logo.png'
import loginBg from '@/assets/login-bg.png'

const router = useRouter()
const formRef = ref<FormInstance>()
const isLoginMode = ref(true)
const loading = ref(false)
const rememberMe = ref(false)
const allowRegistration = ref(false)

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/settings/public')
    allowRegistration.value = data.allow_registration
  } catch (err) {
    console.error('Failed to load public settings', err)
  }
})

const form = reactive({
  username: '',
  password: '',
  role: 'admin' // default for registration
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: '账号不可为空', trigger: 'blur' }],
  password: [{ required: true, message: '密码不可为空', trigger: 'blur' }]
})

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (isLoginMode.value) {
          // OAuth2 Password Request Form Requires Form Data Native Payload
          const formData = new URLSearchParams()
          formData.append('username', form.username)
          formData.append('password', form.password)

          const { data } = await axios.post('/api/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
          })
          
          // Store token
          localStorage.setItem('itom_token', data.access_token)
          // Set Axios default Auth Header globally
          axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
          
          ElMessage.success('登录成功，欢迎回来')
          router.push('/dashboard')
        } else {
          // Registration uses JSON Pydantic payload
          await axios.post('/api/auth/register', {
            username: form.username,
            password: form.password,
            role: form.role
          })
          
          ElMessage.success('账号注册成功！请切换回登录页登录')
          isLoginMode.value = true
        }
      } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '验证请求失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>
