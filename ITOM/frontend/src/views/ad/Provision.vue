<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">AD 域用户开通向导</h1>
    </div>

    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl overflow-visible">
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules"
        label-position="top"
        class="max-w-2xl"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <el-form-item label="登录账号 (拼音)" prop="new_username">
            <el-input 
              v-model="form.new_username" 
              placeholder="例如: zhangsan"
              :prefix-icon="User"
            />
            <div class="text-xs text-gray-400 mt-1">系统会自动为您拼接 @domain</div>
          </el-form-item>

          <el-form-item label="显示名称 (中文)" prop="new_display_name">
            <el-input 
              v-model="form.new_display_name" 
              placeholder="例如: 张三" 
              :prefix-icon="Postcard"
            />
          </el-form-item>

          <el-form-item label="初始密码" prop="password" class="md:col-span-2">
            <el-input 
              v-model="form.password" 
              type="password" 
              show-password
              placeholder="必须符合域控密码复杂度要求"
              :prefix-icon="Lock"
            />
          </el-form-item>

          <el-form-item label="所属组织单元 (OU)" prop="ou_path" class="md:col-span-2">
            <el-select 
              v-model="form.ou_path" 
              placeholder="请选择部门节点"
              class="w-full"
              filterable
              :loading="loading.ou"
            >
              <el-option
                v-for="item in ouOptions"
                :key="item.dn"
                :label="item.name"
                :value="item.dn"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="职位/岗位 (选填)" prop="position_name">
            <el-select 
              v-model="form.position_name" 
              placeholder="请选择员工岗位"
              class="w-full"
              filterable
              clearable
            >
              <el-option
                v-for="pos in positionOptions"
                :key="pos.name"
                :label="pos.name"
                :value="pos.name"
              >
                <span class="float-left">{{ pos.name }}</span>
                <span class="float-right text-gray-400 text-sm">{{ pos.suffix }}</span>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="附加安全组 (选填)" prop="groups" class="md:col-span-2">
            <el-select 
              v-model="form.groups" 
              multiple 
              placeholder="为用户分配特定网络或业务权限组"
              class="w-full"
              filterable
              :loading="loading.groups"
            >
              <el-option
                v-for="item in groupOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </div>

        <div class="mt-8 flex justify-end space-x-4 border-t pt-6">
          <el-button @click="resetForm">重置表单</el-button>
          <el-button 
            type="primary" 
            auto-insert-space 
            :loading="submitting"
            @click="submitForm"
            class="bg-indigo-600 hover:bg-indigo-700 border-none"
          >
            立即开通账号
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { User, Lock, Postcard } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'

const formRef = ref<FormInstance>()
const submitting = ref(false)

const loading = reactive({
  ou: false,
  groups: false
})

const ouOptions = ref<{dn: string, name: string}[]>([])
const groupOptions = ref<string[]>([])
const positionOptions = ref<{name: string, suffix: string}[]>([])

const form = reactive({
  new_username: '',
  new_display_name: '',
  password: '',
  ou_path: '',
  position_name: '',
  groups: [] as string[]
})

const rules = reactive<FormRules>({
  new_username: [
    { required: true, message: '请输入账户名拼音', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  new_display_name: [
    { required: true, message: '请输入中文显示名称', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' }
  ],
  ou_path: [
    { required: true, message: '请选择组织单元 (OU)', trigger: 'change' }
  ]
})

const fetchOptions = async () => {
  try {
    loading.ou = true
    // 为了简化测试我们先写死一个 mock user token 或假设后端去除了测试期间强校验
    // 注：若你启用了强 JWT 校验，需在 axios 发请求前置入 token header
    
    // 我们先尝试直接调用路由获取 OU
    const { data: ous } = await axios.get('/api/ad/ous')
    ouOptions.value = ous
  } catch (err: any) {
    ElMessage.warning('拉取 OU 列表失败，可能是当前并未登录或 AD 配置未联通: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.ou = false
  }

  try {
    const { data: config } = await axios.get('/api/settings/')
    if (config.POSITIONS) {
      positionOptions.value = config.POSITIONS
    }
    if (config.DEFAULT_USER_PASSWORD && !form.password) {
      form.password = config.DEFAULT_USER_PASSWORD
    }
  } catch (err) {
    console.error('拉取全局配置失败', err)
  }

  try {
    loading.groups = true
    const { data } = await axios.get('/api/ad/groups')
    groupOptions.value = data.groups
  } catch (err) {
    console.error('获取群组失败', err)
  } finally {
    loading.groups = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const { data } = await axios.post('/api/ad/users', form)
        if (data.success) {
          ElMessage.success('域用户创建成功: ' + data.message)
          resetForm()
        }
      } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '用户创建失败，请检查网络或 AD 日志')
      } finally {
        submitting.value = false
      }
    }
  })
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

onMounted(() => {
  fetchOptions()
})
</script>
