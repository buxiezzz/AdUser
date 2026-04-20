<template>
  <div class="space-y-6">
    <!-- Top Greeting -->
    <div class="bg-white rounded-2xl shadow-sm p-4 border border-gray-100 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <el-avatar :size="48" class="bg-blue-100 text-primary font-bold">A</el-avatar>
        <div>
          <h2 class="font-bold text-gray-800">您好, 管理员</h2>
          <p class="text-xs text-gray-400 mt-0.5">欢迎使用 ITOM 移动门户</p>
        </div>
      </div>
    </div>

    <!-- Application Grid -->
    <div v-for="group in menuConfig" :key="group.title" class="space-y-3">
      <h3 class="text-sm font-bold text-gray-500 flex items-center ml-1">
         <el-icon class="mr-1.5"><component :is="allIcons[group.icon] || group.icon" /></el-icon>
         {{ group.title }}
      </h3>
      <div class="grid grid-cols-2 gap-3">
        <!-- 无子菜单 -->
        <template v-if="!group.children || group.children.length === 0">
           <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 active:scale-95 transition-all aspect-square" @click="navigateTo(group.path)">
              <div class="w-12 h-12 rounded-xl bg-blue-50 text-primary flex items-center justify-center text-xl mb-3">
                 <el-icon><component :is="allIcons[group.icon] || group.icon" /></el-icon>
              </div>
              <span class="text-xs font-semibold text-gray-700 text-center">{{ group.title }}</span>
           </div>
        </template>
        <!-- 有子菜单 -->
        <template v-else>
           <div v-for="sub in group.children" :key="sub.title" class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 active:scale-95 transition-all aspect-square" @click="navigateTo(sub.path)">
              <div class="w-12 h-12 rounded-xl bg-blue-50 text-primary flex items-center justify-center text-xl mb-3">
                 <el-icon><component :is="allIcons[sub.icon] || sub.icon" /></el-icon>
              </div>
              <span class="text-xs font-semibold text-gray-700 text-center">{{ sub.title }}</span>
           </div>
        </template>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { menuConfig } from '../../router/menu'
import * as Icons from '@element-plus/icons-vue'

const router = useRouter()
const allIcons = Icons as Record<string, any>

const navigateTo = (path: string) => {
    // 全自动套上套壳
    router.push(`/mobile${path}`)
}
</script>
