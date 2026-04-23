<template>
  <div class="min-h-screen bg-gray-50 flex flex-col font-sans">
    <!-- Top Header for Mobile Navigation -->
    <div class="bg-gradient-to-r from-red-600 to-red-700 text-white sticky top-0 z-50 px-4 py-3 flex items-center shadow-lg border-b border-red-500/20">
      <el-icon v-if="!isHome" class="mr-3 text-xl cursor-pointer" @click="goBack">
        <ArrowLeft />
      </el-icon>
      <img v-else :src="logo" class="h-8 w-auto mr-3 filter brightness-0 invert" alt="SK" />
      <h1 class="text-lg font-bold flex-1 truncate">{{ currentTitle }}</h1>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-y-auto p-4 content-area">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import logo from '@/assets/logo.png'

const route = useRoute()
const router = useRouter()

const currentTitle = computed(() => route.meta.title || '移动端应用中心')
const isHome = computed(() => route.path === '/mobile' || route.path === '/mobile/index')

const goBack = () => {
    // 尽量安全返回，没有历史记录则回主页
    if (window.history.length > 1) {
        router.back()
    } else {
        router.push('/mobile')
    }
}
</script>

<style scoped>
/* 针对降级后的桌面端大表格在手机上可能产生的横向溢出 */
.content-area {
  -webkit-overflow-scrolling: touch;
}

:deep(.el-table) {
  width: 100% !important;
}
</style>
