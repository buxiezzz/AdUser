<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-6 sm:px-6 lg:px-8 bg-gradient-to-br from-indigo-900 via-blue-900 to-indigo-800 relative overflow-hidden">
    <!-- Fancy background elements -->
    <div class="absolute -top-20 -right-20 w-64 h-64 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
    <div class="absolute -bottom-20 -left-20 w-64 h-64 bg-emerald-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>

    <div class="relative z-10 w-full max-w-sm mx-auto flex flex-col items-center">
      <div class="inline-flex items-center justify-center p-3 bg-white/10 rounded-2xl backdrop-blur-md border border-white/20 shadow-2xl mb-4">
        <el-icon :size="48" class="text-white"><Monitor /></el-icon>
      </div>
      
      <h1 class="text-3xl font-extrabold text-white tracking-tight mb-2">ITOM 移动端</h1>
      <p class="text-indigo-200 text-sm mb-12 text-center">智能资产流转与管理工作台</p>

      <!-- Big Scan Button -->
      <button 
        @click="$router.push('/mobile/scan')"
        class="w-full relative group bg-indigo-600 hover:bg-indigo-700 text-white rounded-3xl p-1 mb-6 transition-all shadow-xl hover:shadow-2xl hover:-translate-y-1 overflow-hidden backdrop-blur-sm"
      >
        <div class="absolute inset-0 bg-white/20 rounded-3xl blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
        <div class="relative bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-[22px] py-4 px-6 flex items-center justify-center font-bold text-lg border border-indigo-400/30">
          <el-icon :size="24" class="mr-3"><FullScreen /></el-icon>
          <span class="tracking-widest">扫一扫标签</span>
        </div>
      </button>

      <!-- Go to PC Admin Mode -->
      <button 
        @click="goToAdmin"
        class="w-full bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-[22px] py-3 px-6 flex items-center justify-center font-medium transition-colors shadow-sm backdrop-blur-md"
      >
        <el-icon :size="20" class="mr-2"><Setting /></el-icon>
        进入完整管理控制台
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Monitor, FullScreen, Setting } from '@element-plus/icons-vue'

const router = useRouter()

const goToAdmin = () => {
    // 设置临时标识，允许当前会话强制进入 PC 模式
    sessionStorage.setItem('itom_force_pc', '1')
    router.push('/login')
}
</script>

<style scoped>
@keyframes blob {
  0% { transform: translate(0px, 0px) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0px, 0px) scale(1); }
}

.animate-blob {
  animation: blob 7s infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}
</style>
