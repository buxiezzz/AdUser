<template>
  <div class="min-h-screen bg-gray-100 font-sans text-gray-800 relative pb-20">
    <!-- Top Nav with Admin Portal trigger -->
    <div class="absolute top-4 right-4 z-10 transition-all flex flex-wrap justify-end gap-2 max-w-[85%]">
      <div v-if="!isAuthenticated" @click="showLogin = true" class="bg-black/20 backdrop-blur text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer">
        <el-icon><Avatar /></el-icon> <span>管理入口</span>
      </div>
      <template v-else>
        <div v-if="asset && asset.status !== '闲置'" @click="returnAsset" class="bg-emerald-500/90 backdrop-blur text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer shadow-sm">
          <el-icon><RefreshLeft /></el-icon> <span>退库</span>
        </div>
        <div @click="triggerMobilePrint" class="bg-indigo-500/90 backdrop-blur text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer shadow-sm">
          <el-icon><Printer /></el-icon> <span>打印标签</span>
        </div>
        <div @click="openReassignDialog" class="bg-yellow-600/90 backdrop-blur text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer shadow-sm">
          <el-icon><User /></el-icon> <span>修改归属</span>
        </div>
        <div @click="$router.push('/mobile/asset/create')" class="bg-blue-500/90 backdrop-blur text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer shadow-sm">
          <el-icon><Plus /></el-icon> <span>录入</span>
        </div>
        <div @click="logout" class="bg-red-500/80 backdrop-blur text-white text-xs px-3 py-1.5 rounded-full flex items-center gap-1 cursor-pointer shadow-sm">
          <el-icon><SwitchButton /></el-icon> <span>退出</span>
        </div>
      </template>
    </div>
    
    <div class="p-4 pt-14">
      <div v-if="loading" class="flex flex-col items-center justify-center mt-20">
      <el-spinner class="text-blue-500 mb-4 text-3xl"/>
      <p class="text-sm text-gray-500">正在查询资产档案...</p>
    </div>

    <div v-else-if="error" class="flex flex-col items-center justify-center mt-20 p-6 bg-white rounded-xl shadow-sm text-center">
      <el-icon class="text-red-400 text-5xl mb-4"><WarnTriangleFilled /></el-icon>
      <h2 class="text-lg font-bold mb-2">资产查询失败</h2>
      <p class="text-sm text-gray-500 mb-6">{{ error }}</p>
      <el-button type="primary" round class="w-full max-w-[200px]" @click="fetchAssetDetail">重试</el-button>
    </div>

    <div v-else-if="asset" class="pb-10">
       <!-- Header Card -->
       <div class="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-5 text-white shadow-md relative overflow-hidden mb-4">
         <div class="absolute -right-4 -top-4 opacity-10 text-8xl pointer-events-none">📱</div>
         <h1 class="text-2xl font-bold mb-1 break-all pr-12">{{ getCategoryName() }}</h1>
         <p class="text-blue-100 text-xs tracking-wider font-mono opacity-80">{{ asset.asset_code }}</p>
         
         <div class="mt-4 flex gap-2">
            <span class="px-2.5 py-1 rounded text-xs font-medium border border-white/20" :class="statusClass(asset.status)">
              {{ asset.status }}
            </span>
            <span v-if="asset.dynamic_attributes?.['规格型号']" class="px-2.5 py-1 bg-white/10 rounded text-xs font-medium border border-white/20">
              型号: {{ asset.dynamic_attributes['规格型号'] }}
            </span>
         </div>
       </div>

       <!-- Core Info -->
       <div class="bg-white rounded-xl p-0 shadow-sm mb-4 overflow-hidden border border-gray-100">
         <div class="p-4 bg-gray-50/50 border-b border-gray-100 flex items-center">
            <el-icon class="text-blue-500 mr-2 text-lg"><User /></el-icon>
            <h2 class="font-bold text-gray-700">使用归属</h2>
         </div>
         <div class="p-4 grid grid-cols-2 gap-y-4">
           <div>
             <p class="text-xs text-gray-400 mb-1">使用人</p>
             <p class="font-medium text-sm">{{ asset.owner ? asset.owner.name : '闲置中' }}</p>
           </div>
           <div>
             <p class="text-xs text-gray-400 mb-1">所属部门</p>
             <p class="font-medium text-sm">{{ asset.owner ? asset.owner.department : '-' }}</p>
           </div>
           <div class="col-span-2" v-if="asset.dynamic_attributes?.['序列号']">
             <p class="text-xs text-gray-400 mb-1">硬件序列号 (SN)</p>
             <p class="font-medium text-sm font-mono tracking-tight">{{ asset.dynamic_attributes['序列号'] }}</p>
           </div>
         </div>
       </div>

       <!-- Dynamic Info -->
       <div v-if="Object.keys(dynamicExtAttrs).length > 0" class="bg-white rounded-xl p-0 shadow-sm border border-gray-100">
         <div class="p-4 bg-gray-50/50 border-b border-gray-100 flex items-center">
            <el-icon class="text-amber-500 mr-2 text-lg"><List /></el-icon>
            <h2 class="font-bold text-gray-700">详细参数</h2>
         </div>
         <div class="divide-y divide-gray-50">
           <div v-for="(val, key) in dynamicExtAttrs" :key="String(key)" class="p-4 flex justify-between items-center">
             <span class="text-sm text-gray-500 whitespace-nowrap">{{ key }}</span>
             <span class="text-sm font-medium text-right break-words pl-4">{{ val || '-' }}</span>
           </div>
         </div>
       </div>
       
       <div class="mt-8 text-center text-xs text-gray-400 pb-16">
         - IT 资产管理中心 -
       </div>
    </div></div>
    

    <!-- Reassign Dialog -->
    <el-dialog v-model="showReassignDialog" title="选择新使用人" width="90%" class="rounded-xl" :show-close="false">
      <div class="pb-4">
         <el-select
            v-model="newOwnerId"
            filterable
            remote
            reserve-keyword
            placeholder="请输入名字或拼音搜索"
            :remote-method="searchEmployees"
            :loading="employeeLoading"
            size="large"
            value-key="id"
            class="w-full"
          >
            <el-option
              v-for="item in employeeOptions"
              :key="item.id"
              :label="`${item.name} (${item.department})`"
              :value="item.id"
            />
          </el-select>
      </div>
      <template #footer>
        <div class="flex gap-3">
          <el-button class="flex-1 !rounded-lg" @click="showReassignDialog = false">取消</el-button>
          <el-button class="flex-1 !rounded-lg" type="primary" @click="submitReassign" :loading="actionLoading" :disabled="!newOwnerId">确认划拨</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Admin Login Dialog -->
    <el-dialog v-model="showLogin" title="管理员验证" width="90%" class="rounded-xl" :show-close="false">
      <el-form :model="loginForm" class="mt-2">
        <el-form-item>
          <el-input v-model="loginForm.username" placeholder="管理账号 / 域账号" prefix-icon="User" size="large"></el-input>
        </el-form-item>
        <el-form-item class="mb-2">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex gap-3 mt-4">
          <el-button class="flex-1 !rounded-lg" @click="showLogin = false">取消</el-button>
          <el-button class="flex-1 !rounded-lg" type="primary" :loading="loginLoading" @click="handleLogin">登录授权</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Hidden Print Area -->
    <div v-if="asset" id="print-area" class="print-only">
        <div style="width: 50mm; height: 30mm; box-sizing: border-box; padding: 2mm; display: flex; flex-direction: column; justify-content: space-between;">
           <table style="width: 100%; height: 100%; border-collapse: collapse; table-layout: fixed; font-family: sans-serif;">
              <tr style="height: 10%;">
                 <td colspan="2" style="border: 1px solid black; padding: 0 2mm; font-size: 10px; font-weight: bold; text-align: center;">- IT 资产标签 -</td>
              </tr>
              <tr style="height: 25%;">
                 <td colspan="2" style="border: 1px solid black; padding: 0 2mm; font-size: 14px; font-weight: bold; text-align: center; white-space: nowrap; overflow: hidden;">{{ asset.category ? asset.category.name : '未知资产' }}</td>
              </tr>
              <tr style="height: 15%;">
                 <td colspan="2" style="border: 1px solid black; padding: 0 2mm; font-size: 9px; white-space: nowrap; overflow: hidden;">资产编号: {{ asset.asset_code }}</td>
              </tr>
              <tr style="height: 15%;">
                 <td colspan="2" style="border: 1px solid black; padding: 0 2mm; font-size: 9px; white-space: nowrap; overflow: hidden;">资产型号: {{ asset.dynamic_attributes?.['规格型号'] || '-' }}</td>
              </tr>
              <tr style="height: 15%;">
                 <td style="border: 1px solid black; padding: 0 2mm; font-size: 9px; border-right: none; white-space: nowrap; overflow: hidden;">序 列 号 : {{ asset.dynamic_attributes?.['序列号'] || '-' }}</td>
                 <td rowspan="2" style="border: 1px solid black; border-left: 1px solid black; padding: 2px; text-align: center; vertical-align: middle; width: 1%;">
                    <qrcode-vue :value="getQrUrl(asset)" :size="24" level="L" render-as="svg" style="display:block; margin: 0 auto;" />
                 </td>
              </tr>
              <tr style="height: 15%;">
                 <td style="border: 1px solid black; padding: 0 2mm; font-size: 8px; border-right: none; white-space: nowrap; overflow: hidden;">使用日期: {{ new Date(asset.created_at).toISOString().split('T')[0] }}</td>
              </tr>
           </table>
        </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { WarnTriangleFilled, User, List, Avatar, SwitchButton, Printer, Plus, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import QrcodeVue from 'qrcode.vue'

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

const route = useRoute()
const qrToken = route.params.token as string
const loading = ref(true)
const error = ref('')
const asset = ref<any>(null)

// Auth & Admin State
const isAuthenticated = ref(!!localStorage.getItem('itom_token'))
const showLogin = ref(false)
const loginLoading = ref(false)
const loginForm = ref({ username: '', password: '' })

// Actions State
const actionLoading = ref(false)

// Reassign State
const showReassignDialog = ref(false)
const employeeOptions = ref<any[]>([])
const employeeLoading = ref(false)
const newOwnerId = ref<number | null>(null)



const fetchAssetDetail = async () => {
    loading.value = true
    error.value = ''
    try {
        const res = await axios.get(`/api/assets/mobile/${qrToken}`)
        asset.value = res.data
    } catch (err: any) {
        error.value = err.response?.data?.detail || '网络请求异常或二维码无效'
    } finally {
        loading.value = false
    }
}

const getCategoryName = () => {
    if(!asset.value?.category) return '未知资产'
    return asset.value.category.name
}

const getQrUrl = (a: any) => {
    if (!a) return window.location.origin
    return a.qr_code_token ? `${window.location.origin}/mobile/asset/${a.qr_code_token}` : window.location.origin
}

const dynamicExtAttrs = computed(() => {
    if (!asset.value || !asset.value.dynamic_attributes) return {}
    const result: Record<string, any> = {}
    const excludes = ['规格型号', '序列号']
    for (const key in asset.value.dynamic_attributes) {
        if (!excludes.includes(key) && asset.value.dynamic_attributes[key]) {
            result[key] = asset.value.dynamic_attributes[key]
        }
    }
    return result
})

const statusClass = (status: string) => {
    if (status === '在用') return 'bg-green-500/20 text-green-100 border-green-400/30'
    if (status === '闲置') return 'bg-yellow-500/20 text-yellow-100 border-yellow-400/30'
    if (status === '维修') return 'bg-orange-500/20 text-orange-100 border-orange-400/30'
    return 'bg-gray-500/20 text-gray-100 border-gray-400/30' // 报废
}

onMounted(() => {
    if (!qrToken) {
        error.value = '扫码参数缺失'
        loading.value = false
        return
    }
    fetchAssetDetail()
})

// Authentication Handlers
const handleLogin = async () => {
    if (!loginForm.value.username || !loginForm.value.password) {
        ElMessage.warning('请输入账号和密码')
        return
    }
    loginLoading.value = true
    try {
        const formData = new URLSearchParams()
        formData.append('username', loginForm.value.username)
        formData.append('password', loginForm.value.password)
        
        const res = await axios.post('/api/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
        localStorage.setItem('itom_token', res.data.access_token)
        isAuthenticated.value = true
        showLogin.value = false
        ElMessage.success('授权成功')
        loginForm.value = { username: '', password: '' } // Reset
    } catch (err) {
        ElMessage.error('账号或密码错误')
        localStorage.removeItem('itom_token')
        isAuthenticated.value = false
    } finally {
        loginLoading.value = false
    }
}

const logout = () => {
    localStorage.removeItem('itom_token')
    isAuthenticated.value = false
    ElMessage.info('已退出管理模式')
}

// Action Handlers
const triggerMobilePrint = () => {
   // Small timeout to avoid freezing main thread for print dialog instantly
   setTimeout(() => {
     window.print()
   }, 300)
}

const openReassignDialog = () => {
    if (!asset.value) return
    newOwnerId.value = null
    employeeOptions.value = []
    showReassignDialog.value = true
}

const returnAsset = async () => {
    if (!asset.value) return
    try {
        await ElMessageBox.confirm('确定要将该设备强制退回仓库吗？这会同步清除使用人和组织信息。', '退库确认', {
            confirmButtonText: '强制退库',
            cancelButtonText: '取消',
            type: 'warning',
            customClass: 'rounded-xl'
        })
    } catch { return }

    const loading = ElMessage({
        message: '正在处理退库...',
        type: 'info',
        duration: 0
    })

    try {
       const res = await axios.patch(`/api/assets/${asset.value.id}/status`, {
           status: '闲置'
       })
       asset.value = res.data
       loading.close()
       ElMessage.success('设备已成功退库')
    } catch (err: any) {
       loading.close()
       ElMessage.error(err.response?.data?.detail || '退库失败')
       if (err.response?.status === 401) logout()
    }
}

const searchEmployees = async (query: string) => {
    if (query) {
        employeeLoading.value = true
        try {
            const res = await axios.get('/api/assets/employees', { params: { keyword: query } })
            employeeOptions.value = res.data
        } catch (err) {
            console.error(err)
        } finally {
            employeeLoading.value = false
        }
    } else {
        employeeOptions.value = []
    }
}

const submitReassign = async () => {
    if (!asset.value || !newOwnerId.value) return
    const currentOwnerId = asset.value.owner ? asset.value.owner.id : null
    if (newOwnerId.value === currentOwnerId) {
        showReassignDialog.value = false
        return
    }
    
    actionLoading.value = true
    try {
       const res = await axios.patch(`/api/assets/${asset.value.id}/reassign`, {
           owner_id: newOwnerId.value
       })
       // Local optimistic update matching response
       asset.value = { ...asset.value, owner: res.data.owner }
       ElMessage.success('资产归属人已调拨')
       showReassignDialog.value = false
    } catch (err: any) {
       ElMessage.error(err.response?.data?.detail || '调拨失败')
       if (err.response?.status === 401) logout()
    } finally {
       actionLoading.value = false
    }
}
</script>

<style scoped>
.print-only {
  display: none;
}

@media print {
  /* Hide all generic elements */
  body * {
    visibility: hidden;
  }
  
  /* Show only the print area */
  #print-area, #print-area * {
    visibility: visible;
  }
  
  /* Position it perfectly */
  #print-area {
    position: absolute;
    left: 0;
    top: 0;
    margin: 0;
    padding: 0;
  }

  /* Optimize page size for label printer */
  @page {
    size: 50mm 30mm;
    margin: 0;
  }
}
</style>
