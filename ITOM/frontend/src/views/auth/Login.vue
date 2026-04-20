<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gradient-to-br from-indigo-900 via-blue-900 to-indigo-800">
    
    <div class="sm:mx-auto sm:w-full sm:max-w-md mt-[-5%] mb-4 text-center">
      <div class="inline-flex items-center justify-center p-3 bg-white/10 rounded-2xl backdrop-blur-md border border-white/20 shadow-2xl mb-4">
        <el-icon :size="48" class="text-white"><Monitor /></el-icon>
      </div>
      <h2 class="text-center text-3xl font-extrabold text-white tracking-tight">
        ITOM 运维中枢平台
      </h2>
      <p class="mt-2 text-center text-sm text-indigo-200">
        登录以访问资产与统一身份管理基座
      </p>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white/95 backdrop-blur-xl py-8 px-4 shadow-2xl ring-1 ring-gray-900/5 sm:rounded-2xl sm:px-10">
        
        <!-- Toggle Login/Register -->
        <div class="flex border-b border-gray-200 mb-8" v-if="allowRegistration">
          <button 
            @click="isLoginMode = true"
            :class="['flex-1 pb-4 text-sm font-medium transition-colors', isLoginMode ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-700']"
          >
            系统登入
          </button>
          <button 
            @click="isLoginMode = false"
            :class="['flex-1 pb-4 text-sm font-medium transition-colors', !isLoginMode ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-700']"
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
              <a href="#" class="font-medium text-indigo-600 hover:text-indigo-500">
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
            style="background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%); border: none;"
          >
            {{ isLoginMode ? '验证并登入' : '提交注册' }}
          </el-button>
        </el-form>
        
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import axios from 'axios'

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
