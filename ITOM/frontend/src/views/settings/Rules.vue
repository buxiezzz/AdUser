<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">外包装与命名规范</h1>
      <el-button type="primary" :icon="DocumentChecked" @click="saveRules">提交通用规则</el-button>
    </div>

    <!-- 顶部状态提示 -->
    <el-alert
      title="这些设定会影响在『AD 域用户开通向导』中，自动生成的属性（例如强制使用特定域名后缀、强校验 AD 账号格式，以及不同区域默认绑定的附加组）。这也正是本系统高度弹性的体现。"
      type="success"
      show-icon
      :closable="false"
      class="border border-green-100"
    />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- 账号核心命名规则 -->
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <template #header>
          <div class="flex items-center text-gray-800 font-semibold">
            <el-icon class="mr-2 text-indigo-500"><SetUp /></el-icon>
            账号主键约束
          </div>
        </template>
        
        <el-form label-position="top" class="mt-2">
          <el-form-item label="统一域名后缀 (UPN Suffix)">
            <el-input v-model="rules.domain_name" placeholder="例如: corp.example.com">
              <template #prepend>@</template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="企业初始默认密码">
            <el-input v-model="rules.default_password" show-password type="password" placeholder="当管理员留空时使用的默认高强随机密码种子" />
            <div class="text-xs text-amber-500 mt-1">此行为可能会触犯某些域策略，请确保它符合复杂性要求。</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 地区化与业务线隔离配置 -->
      <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
        <template #header>
          <div class="flex items-center text-gray-800 font-semibold">
            <el-icon class="mr-2 text-blue-500"><MapLocation /></el-icon>
            地区过滤器策略池 (Region Options)
          </div>
        </template>

        <div class="space-y-4">
          <div class="text-sm text-gray-500 mb-2">配置全局的 OU 隔离可见性。运维人员在建立账号时将只能看到被激活地点的 OU（如果是 'all' 则显示全部 OU）。</div>
          
          <el-form label-position="top">
            <el-form-item label="当前全局生效地区">
              <el-select v-model="rules.active_region_code" class="w-full">
                <el-option 
                  v-for="region in rules.region_options" 
                  :key="region.code" 
                  :label="region.name" 
                  :value="region.code" 
                />
              </el-select>
            </el-form-item>
          </el-form>

          <el-divider border-style="dashed" />
          <div class="text-sm text-gray-500 mb-2 font-medium">地区别名策略列表管理</div>
          
          <el-collapse v-model="activeRegion">
            <el-collapse-item v-for="(region, index) in rules.region_options" :key="index" :name="index.toString()">
               <template #title>
                 <span class="font-medium text-gray-700 ml-2">{{ region.name }} <el-tag size="small" type="info" class="ml-2">{{ region.code }}</el-tag></span>
               </template>
               <div class="p-4 bg-gray-50 rounded-lg">
                 <el-form-item label="显示名称">
                   <el-input v-model="region.name" size="small" />
                 </el-form-item>
                 <el-form-item label="地区别名 (Code)">
                   <el-input v-model="region.code" size="small" />
                 </el-form-item>
                 <el-form-item label="匹配关键字 (用逗号分隔)">
                   <el-input v-model="region.keywords" size="small" />
                 </el-form-item>
                 <el-button type="danger" size="small" plain @click="removeRegion(index)">删除此区域</el-button>
               </div>
            </el-collapse-item>
          </el-collapse>

          <el-button type="primary" plain :icon="Plus" class="w-full mt-2" @click="addRegion">
            新增业务区域
          </el-button>
        </div>
      </el-card>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { DocumentChecked, SetUp, MapLocation, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const activeRegion = ref(['0']) // 默认展开第一个

const rules = reactive({
  domain_name: '',
  default_password: '',
  active_region_code: 'all',
  region_options: [] as any[]
})

const fetchConfig = async () => {
  try {
    const { data } = await axios.get('/api/settings/')
    rules.domain_name = data.DOMAIN_NAME
    rules.default_password = data.DEFAULT_USER_PASSWORD
    rules.active_region_code = data.ACTIVE_REGION_CODE || 'all'
    
    // 将数组还原
    rules.region_options = (data.REGION_OPTIONS || []).map((r: any) => ({
      ...r,
      keywords: r.keywords?.join(',') || ''
    }))
  } catch (err: any) {
    ElMessage.error('无法拉取规范配置，请检查网络或登录状态')
  }
}

const addRegion = () => {
  const newIndex = rules.region_options.length
  rules.region_options.push({ code: 'new_region', name: '新区域', keywords: '' })
  activeRegion.value = [newIndex.toString()]
}

const removeRegion = (index: number) => {
  rules.region_options.splice(index, 1)
}

const saveRules = async () => {
  try {
    const payload = {
      domain_name: rules.domain_name,
      default_user_password: rules.default_password,
      active_region_code: rules.active_region_code,
      region_options: rules.region_options.map(r => ({
        ...r,
        keywords: r.keywords.split(',').map((k: string) => k.trim()).filter((k: string) => k)
      }))
    }
    
    const { data } = await axios.post('/api/settings/', payload)
    if (data.success) {
      ElMessage.success('规范规则已安全更新至底层机制。')
    }
  } catch(err: any) {
    ElMessage.error(err.response?.data?.detail || '规则保存失败无权')
  }
}

onMounted(() => {
  fetchConfig()
})
</script>
