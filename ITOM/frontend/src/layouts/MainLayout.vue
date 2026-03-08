<template>
  <el-container class="h-screen bg-gray-50 flex overflow-hidden">
    <!-- Desktop Sidebar -->
    <el-aside width="220px" class="hidden md:flex flex-col bg-indigo-900 text-white shadow-xl shrink-0">
      <div class="h-16 flex items-center justify-center font-bold text-xl tracking-wider border-b border-indigo-800 shrink-0">
        ITOM 管理域
      </div>
      <el-menu
        :default-active="route.path"
        active-text-color="#4f46e5"
        background-color="#312e81"
        class="border-r-0 flex-1 overflow-y-auto"
        text-color="#e0e7ff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>控制台概览</span>
        </el-menu-item>
        
        <el-sub-menu index="assets">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>资产管理</span>
          </template>
          <el-menu-item index="/assets/list">资产台账</el-menu-item>
          <el-menu-item index="/assets/categories">资产分类</el-menu-item>
          <el-menu-item index="/assets/flow">扫码流转大图</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="ad">
          <template #title>
            <el-icon><User /></el-icon>
            <span>身份凭据域</span>
          </template>
          <el-menu-item index="/ad/provision">自动开通向导</el-menu-item>
          <el-menu-item index="/ad/users">域用户检索</el-menu-item>
          <el-menu-item index="/ad/groups">安全组策略</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统底座</span>
          </template>
          <el-menu-item index="/settings/rules">命名规范中心</el-menu-item>
          <el-menu-item index="/settings/system">全局配置</el-menu-item>
          <el-menu-item index="/settings/templates">权限模板配置</el-menu-item>
        </el-sub-menu>
      </el-menu>
      
      <div class="p-4 text-xs text-indigo-400 text-center border-t border-indigo-800 shrink-0">
        ITOM Core v1.0
      </div>
    </el-aside>

    <!-- Mobile Sidebar Drawer -->
    <el-drawer v-model="drawerVisible" direction="ltr" size="240px" :with-header="false" class="md:hidden p-0" body-class="p-0">
      <div class="h-full bg-indigo-900 text-white flex flex-col">
          <div class="h-16 flex items-center justify-center font-bold text-xl tracking-wider border-b border-indigo-800 shrink-0">
            ITOM 管理域
          </div>
          <el-menu
            :default-active="route.path"
            active-text-color="#4f46e5"
            background-color="#312e81"
            class="border-r-0 flex-1 overflow-y-auto"
            text-color="#e0e7ff"
            router
            @select="drawerVisible = false"
          >
            <el-menu-item index="/dashboard">
              <el-icon><Odometer /></el-icon>
              <span>控制台概览</span>
            </el-menu-item>
            
            <el-sub-menu index="assets_m">
              <template #title>
                <el-icon><Monitor /></el-icon>
                <span>资产管理</span>
              </template>
              <el-menu-item index="/assets/list">资产台账</el-menu-item>
              <el-menu-item index="/assets/categories">资产分类</el-menu-item>
              <el-menu-item index="/assets/flow">扫码流转大图</el-menu-item>
            </el-sub-menu>

            <el-sub-menu index="ad_m">
              <template #title>
                <el-icon><User /></el-icon>
                <span>身份凭据域</span>
              </template>
              <el-menu-item index="/ad/provision">自动开通向导</el-menu-item>
              <el-menu-item index="/ad/users">域用户检索</el-menu-item>
              <el-menu-item index="/ad/groups">安全组策略</el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="settings_m">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统底座</span>
              </template>
              <el-menu-item index="/settings/rules">命名规范中心</el-menu-item>
              <el-menu-item index="/settings/system">全局配置</el-menu-item>
              <el-menu-item index="/settings/templates">权限模板配置</el-menu-item>
            </el-sub-menu>

            <el-menu-item index="/mobile/home" class="mt-4 border-t border-indigo-800">
              <el-icon><FullScreen /></el-icon>
              <span>返回移动工作台</span>
            </el-menu-item>
          </el-menu>
      </div>
    </el-drawer>
    
    <el-container class="flex-col min-w-0">
      <el-header class="bg-white shadow-sm flex items-center justify-between px-4 md:px-6 h-16 z-10 shrink-0">
        <div class="flex items-center space-x-2 md:space-x-4">
          <el-button class="md:hidden" text @click="drawerVisible = true" style="padding: 8px">
            <el-icon :size="20"><Menu /></el-icon>
          </el-button>
          <div class="text-gray-600 font-medium tracking-wide hidden sm:block">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentRouteName }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="text-gray-800 font-bold sm:hidden">{{ currentRouteName }}</div>
        </div>
        <div class="flex items-center space-x-2">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="flex items-center cursor-pointer outline-none">
              <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" class="mr-1 md:mr-2" />
              <span class="text-gray-700 text-sm font-medium hidden sm:inline">管理员</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout" class="text-red-500">安全退出</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="p-4 md:p-6 overflow-y-auto bg-gray-50 flex-1">
        <!-- 路由出口 -->
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Odometer, 
  Monitor, 
  User, 
  Setting,
  ArrowDown,
  Menu,
  FullScreen
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const drawerVisible = ref(false)

const currentRouteName = computed(() => {
  return route.meta.title || '控制台概览'
})

const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    localStorage.removeItem('itom_token')
    sessionStorage.removeItem('itom_force_pc')
    ElMessage.success('已安全登出')
    router.push('/login')
  }
}
</script>

<style scoped>
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s cubic-bezier(0.55, 0, 0.1, 1);
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-15px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(15px);
}
/* Ensure the body of drawer removes default padding for flush menu */
:deep(.el-drawer__body) {
  padding: 0;
}
</style>
