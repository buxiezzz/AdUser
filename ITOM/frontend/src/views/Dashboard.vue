<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-800 tracking-tight">ITOM 实时业务大屏</h1>
    
    <!-- 业务核心指标 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <el-card shadow="hover" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <div class="flex items-center">
          <div class="p-3 bg-blue-50 text-primary rounded-lg">
            <el-icon :size="24"><Monitor /></el-icon>
          </div>
          <div class="ml-4">
            <h2 class="text-gray-500 text-sm font-medium">在网数字资产</h2>
            <p class="text-3xl font-bold text-gray-800 mt-1">1,248</p>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <div class="flex items-center">
          <div class="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <el-icon :size="24"><CircleCheck /></el-icon>
          </div>
          <div class="ml-4">
            <h2 class="text-gray-500 text-sm font-medium">AD 健康用户</h2>
            <p class="text-3xl font-bold text-gray-800 mt-1">892</p>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <div class="flex items-center">
          <div class="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <div class="ml-4">
            <h2 class="text-gray-500 text-sm font-medium">闲置/异常设备</h2>
            <p class="text-3xl font-bold text-gray-800 mt-1">34</p>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <div class="flex items-center">
          <div class="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <el-icon :size="24"><MagicStick /></el-icon>
          </div>
          <div class="ml-4">
            <h2 class="text-gray-500 text-sm font-medium">今日扫码流转</h2>
            <p class="text-3xl font-bold text-gray-800 mt-1">12</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 骨架屏占位：近期活动与趋势图 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <el-card shadow="never" class="lg:col-span-2 border-0 ring-1 ring-gray-100 rounded-xl">
        <template #header>
          <div class="card-header font-medium text-gray-700">业务流入趋势</div>
        </template>
        <el-skeleton :rows="8" animated />
      </el-card>
      
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <template #header>
          <div class="card-header font-medium text-gray-700">最新流转审计</div>
        </template>
        <el-skeleton :rows="8" animated />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Monitor, CircleCheck, Warning, MagicStick } from '@element-plus/icons-vue'
</script>
