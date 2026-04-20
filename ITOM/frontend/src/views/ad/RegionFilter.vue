<template>
  <div class="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-12">
    <!-- 头部介绍与管理入口 -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div class="flex flex-col space-y-2">
        <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">地区过滤器</h1>
        <p class="text-gray-500 text-lg">
          选择一个当前工作的物理地区。系统将自动过滤域路径、安全组和命名规范。
        </p>
      </div>
      <el-button :icon="Setting" size="large" @click="openManage" class="!rounded-xl shadow-sm">
        管理地区字典库
      </el-button>
    </div>

    <!-- 主选区 -->
    <div v-loading="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- “全域视图”卡片 -->
      <div 
        class="relative group cursor-pointer transition-all duration-400"
        @click="selectRegion('all')"
      >
        <div 
          :class="[
            'h-full p-8 rounded-3xl border-2 transition-all duration-400 flex flex-col items-center text-center space-y-4 overflow-hidden',
            activeRegionCode === 'all' 
              ? 'border-primary bg-indigo-50/50 ring-8 ring-indigo-50' 
              : 'border-gray-100 bg-white hover:border-indigo-200 hover:shadow-2xl hover:-translate-y-2'
          ]"
        >
          <div :class="['p-5 rounded-2xl shadow-inner', activeRegionCode === 'all' ? 'bg-primary text-white' : 'bg-gray-50 text-gray-400']">
            <el-icon :size="36"><Monitor /></el-icon>
          </div>
          <div>
            <h3 class="text-2xl font-black text-gray-900">全域策略视图</h3>
            <p class="text-sm text-gray-500 mt-2 leading-relaxed italic">关闭所有背景过滤，展示 AD 目录的完整原始数据结构。</p>
          </div>
          <div v-if="activeRegionCode === 'all'" class="absolute -top-1 -right-1">
            <div class="bg-primary text-white p-2 rounded-bl-3xl shadow-lg">
              <el-icon :size="20"><CircleCheckFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 动态地区卡片 -->
      <div 
        v-for="region in regions" 
        :key="region.code"
        class="relative group cursor-pointer transition-all duration-400"
        @click="selectRegion(region.code)"
      >
        <div 
          :class="[
            'h-full p-8 rounded-3xl border-2 transition-all duration-400 flex flex-col items-center text-center space-y-5 overflow-hidden',
            activeRegionCode === region.code 
              ? 'border-emerald-500 bg-emerald-50/50 ring-8 ring-emerald-50' 
              : 'border-gray-100 bg-white hover:border-emerald-200 hover:shadow-2xl hover:-translate-y-2'
          ]"
        >
          <div :class="['p-5 rounded-2xl shadow-inner', activeRegionCode === region.code ? 'bg-emerald-500 text-white' : 'bg-gray-50 text-gray-400']">
            <el-icon :size="36"><Location /></el-icon>
          </div>
          <div class="space-y-2">
            <h3 class="text-2xl font-black text-gray-900">{{ region.name }}</h3>
            <div class="flex flex-wrap justify-center gap-1.5 min-h-[24px]">
              <el-tag 
                v-for="kw in region.keywords" 
                :key="kw" 
                size="small" 
                round
                class="border-0 font-bold"
                :effect="activeRegionCode === region.code ? 'dark' : 'plain'"
                :type="activeRegionCode === region.code ? 'success' : 'info'"
              >
                {{ kw }}
              </el-tag>
            </div>
            <p class="text-xs text-gray-400 font-medium">包含以上任意关键字的 OU 或组将被保留。</p>
          </div>
          <div v-if="activeRegionCode === region.code" class="absolute -top-1 -right-1">
            <div class="bg-emerald-500 text-white p-2 rounded-bl-3xl shadow-lg">
              <el-icon :size="20"><CircleCheckFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty 
        v-if="regions.length === 0 && !loading" 
        description="尚未配置任何业务地区，点击右上角开始添加" 
        class="md:col-span-2 lg:col-span-3 bg-white rounded-3xl border-2 border-dashed border-gray-100 py-16" 
      />
    </div>

    <!-- 底部确认栏 -->
    <div class="fixed bottom-8 left-1/2 -translate-x-1/2 w-full max-w-lg z-50 px-4">
      <div class="bg-dark/90 backdrop-blur-md rounded-2xl p-4 shadow-2xl flex items-center justify-between border border-white/10">
        <div class="flex items-center space-x-3 ml-2">
          <div class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
          <span class="text-white text-sm font-bold">准备应用：{{ activeRegionLabel }}</span>
        </div>
        <el-button 
          type="primary" 
          size="large" 
          :loading="saving" 
          class="!rounded-xl !px-10 font-black shadow-lg hover:rotate-1"
          @click="saveActiveFilter"
        >
          立即锁定地区
        </el-button>
      </div>
    </div>

    <!-- 管理弹出框 -->
    <el-dialog 
      v-model="manageVisible" 
      title="地区字典库管理" 
      width="700px" 
      class="rounded-2xl overflow-hidden"
      destroy-on-close
    >
      <div class="space-y-6">
        <div class="flex justify-between items-center mb-4">
          <span class="text-gray-500 text-sm">定义业务覆盖的物理地区及其自动匹配关键词。</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd" circle />
        </div>

        <el-table :data="regionsList" border class="rounded-xl overflow-hidden shadow-sm">
          <el-table-column label="地区名称" width="150">
            <template #default="{ row }">
              <el-input v-model="row.name" placeholder="如: 北京" class="font-bold" />
            </template>
          </el-table-column>
          <el-table-column label="识别码" width="130">
            <template #default="{ row }">
              <el-input v-model="row.code" placeholder="如: beijing" />
            </template>
          </el-table-column>
          <el-table-column label="关键词 (以逗号分隔)">
            <template #default="{ row }">
              <el-input v-model="row.keywordStr" placeholder="匹配 AD 路径的关键字" @blur="syncKeywords(row)" />
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button :icon="Delete" type="danger" link @click="removeRegion($index)" />
            </template>
          </el-table-column>
        </el-table>

        <div class="bg-orange-50 p-4 rounded-xl flex items-start space-x-3">
          <el-icon class="text-orange-400 mt-0.5"><InfoFilled /></el-icon>
          <p class="text-xs text-orange-800 leading-relaxed">
            注意：删除一个正在使用的地区会导致全系统过滤器回退到“全域视图”。请在删除前确保已解除该地区的关联。
          </p>
        </div>
      </div>
      <template #footer>
        <div class="flex guest-center gap-3">
          <el-button @click="manageVisible = false">取消</el-button>
          <el-button type="primary" :loading="updatingList" @click="saveRegionOptions">保存字典库</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Monitor, Location, CircleCheckFilled, Setting, Plus, Delete, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

interface Region {
  code: string
  name: string
  keywords: string[]
  keywordStr?: string // 临时字段
}

const loading = ref(true)
const saving = ref(false)
const manageVisible = ref(false)
const updatingList = ref(false)
const regions = ref<Region[]>([])
const activeRegionCode = ref('all')

// 用于管理的临时副本
const regionsList = ref<Region[]>([])

const activeRegionLabel = computed(() => {
  if (activeRegionCode.value === 'all') return '全域策略视图'
  const match = regions.value.find(r => r.code === activeRegionCode.value)
  return match ? match.name : activeRegionCode.value
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/settings/')
    regions.value = data.REGION_OPTIONS || []
    activeRegionCode.value = data.ACTIVE_REGION_CODE || 'all'
    
    // 初始化临时副本，将 keywords 数组转为字符串方便编辑
    regionsList.value = JSON.parse(JSON.stringify(regions.value)).map((r: Region) => ({
      ...r,
      keywordStr: r.keywords.join(', ')
    }))
  } catch (err) {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const selectRegion = (code: string) => {
  activeRegionCode.value = code
}

// 切换并锁定过滤器
const saveActiveFilter = async () => {
  saving.value = true
  try {
    const payload = { active_region_code: activeRegionCode.value }
    await axios.post('/api/settings/', payload)
    ElMessage.success({
      message: `工作区域已切换至: ${activeRegionLabel.value}`,
      duration: 3000
    })
  } catch (err: any) {
    ElMessage.error('切换失败')
  } finally {
    saving.value = false
  }
}

// ---- 管理逻辑 ----
const openManage = () => {
  manageVisible.value = true
}

const handleAdd = () => {
  regionsList.value.push({
    name: '新地区',
    code: 'new_region',
    keywords: [],
    keywordStr: ''
  })
}

const removeRegion = (index: number) => {
  regionsList.value.splice(index, 1)
}

const syncKeywords = (row: Region) => {
  if (row.keywordStr) {
    // 按中英文逗号切割并重置
    row.keywords = row.keywordStr.split(/[,，]/).map(s => s.trim()).filter(s => !!s)
  } else {
    row.keywords = []
  }
}

const saveRegionOptions = async () => {
  updatingList.value = true
  try {
    // 清洗掉 keywordStr 字段
    const cleanList = regionsList.value.map(r => ({
      name: r.name,
      code: r.code,
      keywords: r.keywords
    }))
    
    const payload = { region_options: cleanList }
    const { data } = await axios.post('/api/settings/', payload)
    if (data.success) {
      ElMessage.success('地区字典库更新成功')
      manageVisible.value = false
      await fetchData() // 重新拉取首页渲染
    }
  } catch (err: any) {
    ElMessage.error('更新失败')
  } finally {
    updatingList.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
/* 沉浸式动效 */
.duration-400 { transition-duration: 400ms; }
:deep(.el-button--primary) {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  border: none;
}
</style>
