<template>
  <el-container class="h-screen bg-gray-50">
    <el-aside width="220px" class="bg-indigo-900 text-white flex flex-col shadow-xl">
      <div class="h-16 flex items-center justify-center font-extrabold text-xl tracking-widest bg-gradient-to-r from-indigo-900 to-indigo-800 text-white border-b border-white/10 shadow-sm">
        ITOM <span class="text-indigo-300 ml-2">CORE</span>
      </div>
      <el-menu
        :default-active="route.path"
        active-text-color="#ffffff"
        background-color="transparent"
        class="border-r-0 flex-1 overflow-y-auto custom-scrollbar"
        text-color="#c7d2fe"
        router
      >
        <!-- 顶级独立菜单 -->
        <el-menu-item 
          v-for="item in menuConfig.filter(m => !m.children)" 
          :key="item.path" 
          :index="item.path"
          class="hover:bg-white/5 mx-2 my-1 rounded-xl transition-all duration-300"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
        
        <!-- 带子集的动态菜单 -->
        <el-sub-menu 
          v-for="sub in menuConfig.filter(m => m.children)" 
          :key="sub.path" 
          :index="sub.path"
          class="mx-2"
        >
          <template #title>
            <el-icon><component :is="sub.icon" /></el-icon>
            <span>{{ sub.title }}</span>
          </template>
          <el-menu-item 
            v-for="child in sub.children" 
            :key="child.path" 
            :index="child.path"
            class="hover:bg-white/5 my-1 rounded-xl pl-12 transition-all duration-300"
          >
            <el-icon v-if="child.icon" class="scale-90"><component :is="child.icon" /></el-icon>
            <span class="text-sm">{{ child.title }}</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
      
      <div class="p-4 text-xs text-indigo-400 text-center border-t border-indigo-800">
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
              <span class="text-gray-700 text-sm font-medium">管理员</span>
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
      
      <el-main class="p-6 relative overflow-y-auto w-full h-full">
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
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { menuConfig } from '../router/menu'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const currentRouteName = computed(() => {
  return route.meta.title || '控制台概览'
})

const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    localStorage.removeItem('itom_token')
    ElMessage.success('已安全登出')
    router.push('/login')
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #4f46e5 0%, #4338ca 100%) !important;
  color: #ffffff !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-sub-menu__title:hover),
:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: #ffffff !important;
}

:deep(.el-sub-menu.is-active .el-sub-menu__title) {
  color: #ffffff !important;
}

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
</style>
