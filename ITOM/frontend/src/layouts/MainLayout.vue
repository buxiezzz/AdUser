<template>
  <el-container class="h-screen bg-gray-50">
    <el-aside width="240px" class="bg-white flex flex-col border-r border-gray-100 shadow-sm">
      <div class="h-28 flex items-center justify-center bg-white border-b border-gray-50 mb-4 px-4 overflow-hidden">
        <img :src="logo" alt="SK先惠" class="h-16 w-auto transform hover:scale-105 transition-transform" />
      </div>
      <el-menu
        :default-active="route.path"
        active-text-color="#ffffff"
        background-color="transparent"
        class="sidebar-menu flex-1 overflow-y-auto custom-scrollbar"
        text-color="#4b5563"
        unique-opened
        router
      >
        <!-- 统一按 menuConfig 顺序渲染 -->
        <template v-for="item in menuConfig" :key="item.path">
          <el-menu-item
            v-if="!item.children"
            :index="item.path"
            class="menu-item"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>

          <el-sub-menu
            v-else
            :index="item.path"
            class="sub-menu-container"
          >
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.path"
              :index="child.path"
              class="menu-item sub-item pl-12"
            >
              <el-icon v-if="child.icon" class="scale-90"><component :is="child.icon" /></el-icon>
              <span class="text-sm">{{ child.title }}</span>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
      
      <div class="p-4 text-xs text-gray-400 text-center border-t border-gray-50">
        ITOM Core v1.0
      </div>
    </el-aside>
    
    <el-container>
      <el-header class="bg-white shadow-sm flex items-center justify-between px-6 h-16 z-10">
        <div class="text-gray-600 font-medium tracking-wide">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRouteName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="flex items-center space-x-4">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="flex items-center cursor-pointer outline-none">
              <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" class="mr-2" />
              <div class="flex flex-col items-start">
                <span class="text-gray-700 text-sm font-medium leading-tight">{{ userDisplayName }}</span>
                <span v-if="userLocationName" class="text-xs text-indigo-500 leading-tight">{{ userLocationName }}</span>
              </div>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" :icon="User">个人中心(修改密码)</el-dropdown-item>
                <el-dropdown-item divided command="logout" :icon="SwitchButton" class="text-red-500">安全退出系统</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="p-6 relative overflow-y-auto w-full h-full bg-[#f8fafc]">
        <!-- 路由出口 -->
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 (深色玻璃质感) -->
    <el-dialog v-model="changePwdVisible" title="安全设置：修改登录密码" width="420px" append-to-body class="rounded-2xl">
      <el-form :model="pwdForm" label-position="top">
        <el-form-item label="当前原密码" required>
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入您目前的登录密码" />
        </el-form-item>
        <el-form-item label="设定新密码" required>
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入 6 位以上的新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="changePwdVisible = false">取消</el-button>
          <el-button type="primary" :loading="pwdLoading" @click="submitChangePassword">保存新密码</el-button>
        </div>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { menuConfig } from '../router/menu'
import { ElMessage } from 'element-plus'
import { User, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import axios from 'axios'
import logo from '@/assets/logo.png'

const router = useRouter()
const route = useRoute()

const userDisplayName = ref('管理员')
const userLocationName = ref('')

const fetchUserInfo = async () => {
  try {
    const { data } = await axios.get('/api/auth/me')
    userDisplayName.value = data.display_name || data.username || '管理员'
    userLocationName.value = data.location_name || ''
  } catch {
    // 获取用户信息失败时使用默认值
  }
}

// --- 自动登出逻辑 (30分钟无交互自动登出) ---
const INACTIVITY_TIMEOUT = 30 * 60 * 1000 // 30分钟
let inactivityTimer: any = null

const resetInactivityTimer = () => {
  if (inactivityTimer) clearTimeout(inactivityTimer)
  inactivityTimer = setTimeout(() => {
    handleAutoLogout()
  }, INACTIVITY_TIMEOUT)
}

const handleAutoLogout = () => {
  if (!localStorage.getItem('itom_token')) return
  localStorage.removeItem('itom_token')
  ElMessage.warning('由于您长时间未操作，系统已自动登出以保护账户安全')
  router.push('/login')
}

onMounted(() => {
  fetchUserInfo()
  // 注册全局监听事件
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
  events.forEach(evt => {
    window.addEventListener(evt, resetInactivityTimer, true)
  })
  resetInactivityTimer()
})

onUnmounted(() => {
  // 清理
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
  events.forEach(evt => {
    window.removeEventListener(evt, resetInactivityTimer, true)
  })
  if (inactivityTimer) clearTimeout(inactivityTimer)
})
// ------------------------------------

const currentRouteName = computed(() => {
  return route.meta.title || '控制台概览'
})

const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    localStorage.removeItem('itom_token')
    ElMessage.success('已安全登出')
    router.push('/login')
  } else if (command === 'profile') {
    changePwdVisible.value = true
  }
}

// 修改密码逻辑
const changePwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdForm = ref({
  old_password: '',
  new_password: ''
})

const submitChangePassword = async () => {
  if (!pwdForm.value.old_password || !pwdForm.value.new_password) {
    return ElMessage.warning('请完整填写密码信息')
  }
  if (pwdForm.value.new_password.length < 6) {
    return ElMessage.warning('新密码安全强度不足，请至少输入 6 位')
  }
  
  pwdLoading.value = true
  try {
    await axios.post('/api/auth/change-password', pwdForm.value)
    ElMessage.success('密码修改成功，为保障安全请重新登录')
    changePwdVisible.value = false
    // 强制登出
    localStorage.removeItem('itom_token')
    router.push('/login')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '修改失败：原密码输入不正确')
  } finally {
    pwdLoading.value = false
  }
}
</script>

<style scoped>
/* 菜单容器硬件加速 */
.sidebar-menu {
  border-right: none;
  transform: translateZ(0);
  will-change: height;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}

.menu-item {
  margin: 4px 12px;
  border-radius: 12px;
  /* 仅针对必要属性进行动画，降低重排开销 */
  transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), 
              color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.sub-menu-container {
  margin: 0 12px;
}

:deep(.el-sub-menu__title) {
  border-radius: 12px;
  transition: background-color 0.2s;
}

:deep(.el-menu-item.is-active),
:deep(.el-menu-item.is-active i),
:deep(.el-menu-item.is-active span) {
  color: #ffffff !important;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #e51923 0%, #b91c1c 100%) !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(229, 25, 35, 0.2);
}

:deep(.el-sub-menu__title:hover),
:deep(.el-menu-item:hover) {
  background-color: #fef2f2 !important;
}

:deep(.el-menu-item) {
  color: #374151 !important;
}

:deep(.el-sub-menu__title) {
  color: #374151 !important;
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
</style>
