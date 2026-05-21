<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">系统设置</h1>
      <div class="flex space-x-2" v-if="isSuperAdmin">
        <el-button type="default" @click="exportConfig">导出备份</el-button>
        <el-button type="default" @click="triggerImport">导入配置</el-button>
        <el-button type="primary" :icon="DocumentChecked" @click="saveConfig">保存全局设定</el-button>
        
        <!-- 隐藏的导入文件域 -->
        <input 
          type="file" 
          ref="fileInput" 
          accept=".json,.zip" 
          style="display: none;" 
          @change="handleImportConfig" 
        />
      </div>
    </div>

    <!-- 非 admin 用户提示 -->
    <el-alert
      v-if="!isSuperAdmin && userLoaded"
      title="系统配置仅限 admin 管理员账号修改。如需变更域控连接参数或全局安全策略，请联系总管理员。"
      type="warning"
      show-icon
      :closable="false"
      class="border border-amber-200"
    />

    <!-- 顶部状态提示 -->
    <el-alert
      v-if="isSuperAdmin"
      title="此页面的配置将全局统一应用于所有区域（上海、武汉、长沙）。修改域控连接参数后，所有分公司将同步生效。"
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
            <el-icon class="mr-2 text-primary"><Connection /></el-icon>
            Active Directory 主连接参数
            <el-tag v-if="!isSuperAdmin" size="small" type="info" class="ml-2">只读</el-tag>
          </div>
        </template>
        
        <el-form label-position="top" class="mt-2">
          <el-form-item label="域控制器 IP (Domain Controller)">
            <el-input v-model="settings.dc_ip" placeholder="例如: 10.0.0.5" :disabled="!isSuperAdmin" />
          </el-form-item>
          <el-form-item label="系统级通讯服务账号 (Bind Username)">
            <el-input v-model="settings.bind_username" placeholder="系统用来代理创建用户的管理员账号" :disabled="!isSuperAdmin" />
            <div class="text-xs text-gray-400 mt-1">这解决了以前需要每个操作员输自己高权限账号的安全隐患。</div>
          </el-form-item>
          <el-form-item label="服务账号密码 (Bind Password)">
            <el-input v-model="settings.bind_password" type="password" show-password :disabled="!isSuperAdmin" />
          </el-form-item>
          <el-form-item v-if="isSuperAdmin">
            <el-button type="info" plain :icon="Refresh" @click="testAdConnection" :loading="testingConnection">测试并连通 AD</el-button>
          </el-form-item>
        </el-form>
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
              为了演示和测试方便，目前登录页的"注册"按钮是开放的。但在生产环境中，**我们将默认关闭新用户自主注册**，或者要求通过审批。<br/>
              管理员还可以通过这里的控制台动态切换全局的安全模式：
            </p>
            <div class="mt-4 flex items-center space-x-6">
              <el-switch
                v-model="settings.allow_register"
                size="large"
                active-text="开放自主注册"
                inactive-text="仅内部分发账号"
                :disabled="!isSuperAdmin"
              />
              <el-switch
                v-model="settings.audit_log"
                size="large"
                active-text="记录极客级操作审计日志"
                :disabled="!isSuperAdmin"
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
import { DocumentChecked, Connection, Refresh, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const testingConnection = ref(false)
const isSuperAdmin = ref(false)
const userLoaded = ref(false)

const settings = reactive({
  dc_ip: '',
  bind_username: '',
  bind_password: '',
  allow_register: true,
  audit_log: true
})

const fileInput = ref<HTMLInputElement | null>(null)

const fetchUserRole = async () => {
  try {
    const { data } = await axios.get('/api/auth/me')
    isSuperAdmin.value = data.username === 'admin'
  } catch {
    isSuperAdmin.value = false
  } finally {
    userLoaded.value = true
  }
}

const exportConfig = async () => {
  try {
    const token = localStorage.getItem('itom_token')
    const response = await axios.get('/api/settings/export', {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob'
    })
    
    // Create a download link for the blob
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'itom_backup.zip')
    document.body.appendChild(link)
    link.click()
    link.parentNode?.removeChild(link)
    window.URL.revokeObjectURL(url)
    
  } catch (err) {
    ElMessage.error('导出系统配置失败')
  }
}

const triggerImport = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleImportConfig = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  
  const file = target.files[0]
  if (!file) {
    ElMessage.warning('未能读取到文件')
    return
  }
  
  if (!file.name.endsWith('.json') && !file.name.endsWith('.zip')) {
    ElMessage.warning('只能导入 .zip 或 .json 格式的备份文件')
    target.value = ''
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  try {
    const token = localStorage.getItem('itom_token')
    const { data } = await axios.post('/api/settings/import', formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (data.success) {
      ElMessage.success(data.message || '配置导入成功')
      // 重新加载配置并清空文件域
      await fetchConfig()
      target.value = ''
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '导入配置失败')
    target.value = ''
  }
}

const fetchConfig = async () => {
  try {
    const { data } = await axios.get('/api/settings/')
    settings.dc_ip = data.DOMAIN_CONTROLLER_IP || ''
    settings.bind_username = data.BIND_USERNAME || ''
    settings.bind_password = data.BIND_PASSWORD || ''
    settings.allow_register = data.ALLOW_REGISTRATION !== false // default true
    settings.audit_log = data.AUDIT_LOG !== false
  } catch(err) {
    ElMessage.error('无法加载系统设置此页面配置')
  }
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
      audit_log: settings.audit_log
    }
    const token = localStorage.getItem('itom_token')
    const { data } = await axios.post('/api/settings/', payload, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (data.success) {
      ElMessage.success('全局配置已更新并同步至所有区域。')
    }
  } catch(err: any) {
    ElMessage.error(err.response?.data?.detail || '保存配置失败')
  }
}

onMounted(() => {
  fetchUserRole()
  fetchConfig()
})
</script>
