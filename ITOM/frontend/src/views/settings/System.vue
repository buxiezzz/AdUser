<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">系统底座配置</h1>
      <el-button type="primary" :icon="DocumentChecked" @click="saveConfig">保存全局设定</el-button>
    </div>

    <!-- 顶部状态提示 -->
    <el-alert
      title="此页面替代了您旧版 Python 中的 config.json 和 positions.json。这套新架构意味着未来你的主控密码、AD连接配置和规则，都会安全地存放于数据库或核心引擎层，而不再是散落的文本文档。"
      type="info"
      show-icon
      :closable="false"
      class="border border-blue-100"
    />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- AD 通信配置 -->
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <template #header>
          <div class="flex items-center text-gray-800 font-semibold">
            <el-icon class="mr-2 text-indigo-500"><Connection /></el-icon>
            Active Directory 主连接参数
          </div>
        </template>
        
        <el-form label-position="top" class="mt-2">
          <el-form-item label="域控制器 IP (Domain Controller)">
            <el-input v-model="settings.dc_ip" placeholder="例如: 10.0.0.5" />
          </el-form-item>
          <el-form-item label="系统级通讯服务账号 (Bind Username)">
            <el-input v-model="settings.bind_username" placeholder="系统用来代理创建用户的管理员账号" />
            <div class="text-xs text-gray-400 mt-1">这解决了以前需要每个操作员输自己高权限账号的安全隐患。</div>
          </el-form-item>
          <el-form-item label="服务账号密码 (Bind Password)">
            <el-input v-model="settings.bind_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="info" plain :icon="Refresh" @click="testAdConnection" :loading="testingConnection">测试并连通 AD</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 预设参数 / 职位 -->
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <template #header>
          <div class="flex items-center text-gray-800 font-semibold">
            <el-icon class="mr-2 text-emerald-500"><Menu /></el-icon>
            基础选项数据池 (替代 positions.json)
          </div>
        </template>

        <div class="space-y-4">
          <div class="text-sm font-medium text-gray-600">可选职位列表及英文后缀映射</div>
          
          <div v-for="(item, index) in settings.positions" :key="index" class="flex items-center space-x-2 mb-2">
            <el-input v-model="item.name" placeholder="职位名称 (如: 后端开发)" class="flex-1" />
            <el-input v-model="item.suffix" placeholder="英文后缀 (如: bde)" class="w-1/3" />
            <el-button type="danger" :icon="Delete" circle plain @click="removePosition(index)" />
          </div>
          
          <el-button type="primary" plain :icon="Plus" class="w-full mt-2" @click="addPosition">
            新增职位选项
          </el-button>
        </div>
      </el-card>
      
      <!-- 安全性相关卡片 -->
      <el-card shadow="never" class="lg:col-span-2 border-0 ring-1 ring-emerald-50 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50">
        <div class="flex items-start">
          <div class="p-3 bg-white text-emerald-600 rounded-lg shadow-sm">
            <el-icon :size="24"><Lock /></el-icon>
          </div>
          <div class="ml-4 flex-1">
            <h3 class="text-lg font-bold text-gray-800">关于您关心的注册漏洞问题</h3>
            <p class="text-sm text-gray-600 mt-2 leading-relaxed">
              为了演示和测试方便，目前登录页的“注册”按钮是开放的。但在生产环境中，**我们将默认关闭新用户自主注册**，或者要求通过审批。<br/>
              管理员还可以通过这里的控制台动态切换全局的安全模式：
            </p>
            <div class="mt-4 flex items-center space-x-6">
              <el-switch
                v-model="settings.allow_register"
                size="large"
                active-text="开放自主注册"
                inactive-text="仅内部分发账号"
              />
              <el-switch
                v-model="settings.audit_log"
                size="large"
                active-text="记录极客级操作审计日志"
              />
            </div>
          </div>
        </div>
      </el-card>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { DocumentChecked, Connection, Menu, Refresh, Plus, Delete, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const testingConnection = ref(false)

const settings = reactive({
  dc_ip: '',
  bind_username: '',
  bind_password: '',
  allow_register: true,
  audit_log: true,
  positions: [] as any[]
})

const fetchConfig = async () => {
  try {
    const { data } = await axios.get('/api/settings/')
    settings.dc_ip = data.DOMAIN_CONTROLLER_IP || ''
    settings.bind_username = data.BIND_USERNAME || ''
    settings.bind_password = data.BIND_PASSWORD || ''
    settings.allow_register = data.ALLOW_REGISTRATION !== false // default true
    settings.audit_log = data.AUDIT_LOG !== false
    settings.positions = data.POSITIONS || []
  } catch(err) {
    ElMessage.error('无法加载系统设置此页面配置')
  }
}

const addPosition = () => {
  settings.positions.push({ name: '', suffix: '' })
}

const removePosition = (index: number) => {
  settings.positions.splice(index, 1)
}

const testAdConnection = async () => {
  if (!settings.dc_ip || !settings.bind_username || !settings.bind_password) {
    ElMessage.warning('请先填写完整的域控 IP、系统账号及密码才能进行连通性测试')
    return
  }

  testingConnection.value = true
  try {
    const payload = {
      dc_ip: settings.dc_ip,
      username: settings.bind_username,
      password: settings.bind_password
    }
    const token = localStorage.getItem('itom_token')
    const { data } = await axios.post('/api/settings/test-ad', payload, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (data.success) {
      ElMessage.success(data.message || '成功连接与验证AD域控')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || 'AD 域控连接或验证失败')
  } finally {
    testingConnection.value = false
  }
}

const saveConfig = async () => {
  try {
    const payload = {
      domain_controller_ip: settings.dc_ip,
      bind_username: settings.bind_username,
      bind_password: settings.bind_password,
      allow_registration: settings.allow_register,
      audit_log: settings.audit_log,
      positions: settings.positions
    }
    const token = localStorage.getItem('itom_token')
    const { data } = await axios.post('/api/settings/', payload, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (data.success) {
      ElMessage.success('全局底座配置已向核心引擎下发完成。')
    }
  } catch(err: any) {
    ElMessage.error(err.response?.data?.detail || '保存配置失败')
  }
}

onMounted(() => {
  fetchConfig()
})
</script>
