<template>
  <div class="p-6 space-y-6">
    <!-- 顶部状态卡片 -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ pageTitle }}</h1>
        <p class="text-sm text-gray-500 mt-1">记录系统核心业务数据的变更轨迹，确保运维行为合规可审计。</p>
      </div>
      <el-button @click="fetchLogs" :icon="Refresh" circle shadow="always" />
    </div>

    <!-- 过滤器与报表概览 (可选扩充) -->
    <el-card shadow="never" class="border-gray-100 rounded-2xl">
      <div class="flex items-center space-x-4">
        <el-input
          v-model="queryParams.target"
          placeholder="搜索目标标识 (如资产号、用户名)"
          class="max-w-xs"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          unlink-panels
          clearable
          @change="handleDateChange"
        />
        
        <el-button type="primary" :icon="Search" @click="handleSearch">筛选</el-button>
      </div>
    </el-card>

    <!-- 日志列表主体 -->
    <el-card shadow="never" class="border-gray-100 rounded-3xl overflow-hidden mt-4">
      <el-table 
        :data="logs" 
        v-loading="loading" 
        stripe 
        style="width: 100%"
        :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: 'bold' }"
      >
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-600 font-mono text-xs">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="操作账号" width="150" />
        
        <el-table-column prop="action" label="动作类型" width="160">
          <template #default="{ row }">
            <el-tag :type="getActionTag(row.action)" effect="plain" class="rounded-lg">
              {{ getActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="target" label="目标标识" width="200">
          <template #default="{ row }">
            <span class="font-bold text-primary-dark">{{ row.target }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="details" label="变更详情">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.details"
              effect="dark"
              placement="top"
              :content="formatDetails(row)"
            >
              <span class="text-sm text-gray-600 cursor-help break-all leading-relaxed py-1 block">
                {{ formatDetails(row) }}
              </span>
            </el-tooltip>
            <span v-else class="text-gray-300">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="device_source" label="来源终端" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.device_source" :type="row.device_source.includes('手机') ? 'warning' : 'primary'" effect="plain" class="rounded-lg" size="small">
              {{ row.device_source }}
            </el-tag>
            <span v-else class="text-gray-300">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
      </el-table>

      <div class="mt-6 flex justify-end">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
          class="pb-4"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { Refresh, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()

// 根据路由参数确定模块 (asset 或 ad)
const currentModule = computed(() => route.meta.module as string || 'asset')
const pageTitle = computed(() => currentModule.value === 'asset' ? '资产操作日志' : '域账号操作日志')

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const dateRange = ref([])

const queryParams = reactive({
  page: 1,
  limit: 20,
  target: '',
  module: currentModule.value
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/audit/', {
      params: {
        module: currentModule.value,
        skip: (queryParams.page - 1) * queryParams.limit,
        limit: queryParams.limit,
        target: queryParams.target
      }
    })
    logs.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('Failed to fetch logs', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchLogs()
}

const handleDateChange = (val: any) => {
  // 暂时仅在前端简单记录，如需后端过滤需扩充 API
  console.log('Date changed', val)
}

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const getActionTag = (action: string) => {
  if (action.includes('CREATE') || action === 'PROVISION') return 'success'
  if (action.includes('DELETE')) return 'danger'
  if (action.includes('UPDATE') || action.includes('RESET') || action === 'MOVE_OU') return 'warning'
  if (action.includes('EXPORT') || action.includes('DOWNLOAD')) return 'info'
  return 'info'
}

const actionMap: Record<string, string> = {
  // AD 模块
  'PROVISION': '开通了新账号',
  'PASSWORD_RESET': '重置了登录密码',
  'MOVE_OU': '调整了所属部门(OU)',
  'GROUP_UPDATE': '修改了安全组权限',
  'STATUS_UPDATE': '切换了账号启用状态',
  'EXPORT_USERS': '导出了员工名单',
  'UPDATE_GROUP_MEMBERS': '全量同步了组员',
  
  // 资产模块
  'CREATE': '登记入库了新资产',
  'UPDATE': '修改了资产配置',
  'DELETE_SOFT': '将资产移入回收站',
  'DELETE_HARD': '彻底删除了资产数据',
  'BATCH_DELETE_HARD': '批量彻底删除了资产',
  'BATCH_COPY': '批量复制了资产记录',
  'IMPORT_EXCEL': '通过Excel批量导入',
  'CREATE_CATEGORY': '创建了新的资产分类',
  'DELETE_CATEGORY': '删除了资产分类',
  'TRANSFER_CREATE': '发起了调拨申请',
  'TRANSFER_SHIP': '资产已手动出库',
  'TRANSFER_RECEIVE': '确认签收了资产',
  'TRANSFER_REJECT': '驳回了调拨申请',
  'TRANSFER_APPROVE': '审核通过调拨申请',
  'TRANSFER_BATCH_CREATE': '批量发起了调拨',
  'STOCK_CHECK': '提交了盘点核对',
  
  // 账户与权限管理 (系统账号)
  'CREATE_ACCOUNT': '创建了系统管理员',
  'UPDATE_ACCOUNT': '修改了管理员信息',
  'DELETE_ACCOUNT': '删除了系统管理员',
  'CREATE_LOCATION': '新增了归属地',
  'UPDATE_LOCATION': '修改了归属地信息',
  'DELETE_LOCATION': '删除了归属地',
  
  // 系统设置
  'UPDATE_SETTINGS': '更新了全局系统参数'
}

const assetFieldMap: Record<string, string> = {
  'asset_code': '资产编号',
  'category_id': '设备分类',
  'status': '资产状态',
  'owner_id': '使用人',
  'location_id': '归属地',
  'dynamic_attributes': '扩展属性/动态参数',
  'qr_code_token': '二维码票据',
  'name': '名称/描述'
}

const getActionLabel = (action: string) => {
  return actionMap[action] || action
}

// ---- 口语化解析逻辑 ----

// 简化 DN 路径，仅保留关键部门名
const simplifyDN = (dn: string) => {
  if (!dn) return ''
  // 提取所有的 OU= 或 CN= 后的内容
  const parts = dn.split(',').filter(p => p.includes('='))
  const names = parts.map(p => p.split('=')[1]).filter(n => n && n.toUpperCase() !== 'DC')
  // 如果路径很长，只取前两个和最后一个（或者简单反转展示）
  names.reverse()
  if (names.length > 3) {
    return `${names[0]} > ... > ${names[names.length-1]}`
  }
  return names.join(' > ')
}

const formatDetails = (row: any) => {
  if (!row.details) return '-'
  
  let details: any = null
  let isJson = false
  try {
    // 尝试解析 JSON
    const parsed = JSON.parse(row.details)
    if (typeof parsed === 'object' && parsed !== null) {
      details = parsed
      isJson = true
    } else {
      details = parsed // 可能是单纯的数字或带引号的字符串
    }
  } catch (e) {
    details = row.details // 纯文本
  }

  const action = row.action

  // 如果是纯文本描述（非 JSON 结构），直接应用口语化正则并返回
  if (!isJson) {
    const text = String(details)
    return text
      .replace('发起了调拨申请：', '')
      .replace('一键批量发起了调拨申请：', '一键批量调往')
      .replace(' -> ', ' 调往 ')
  }

  // 以下处理 JSON 结构的详情
  switch (action) {
    case 'PROVISION':
      return `姓名: ${details.display_name || '-'} | 部门: ${simplifyDN(details.ou)} | 职位: ${details.position || '默认'}`
    
    case 'STATUS_UPDATE':
      return details.enabled ? '管理员启用了该域账号' : '管理员禁用了该域账号'
    
    case 'PASSWORD_RESET':
      return '已重置用户登录密码'
    
    case 'MOVE_OU':
      return `部门调整: [旧] ${simplifyDN(details.old_dn)} -> [新] ${simplifyDN(details.new_dn)}`
    
    case 'GROUP_UPDATE': {
      const oldLen = Array.isArray(details.old) ? details.old.length : 0
      const newLen = Array.isArray(details.new) ? details.new.length : 0
      if (newLen > oldLen) return `分配了 ${newLen - oldLen} 个新权限组`
      if (newLen < oldLen) return `移除了 ${oldLen - newLen} 个权限组`
      return `重新同步了 ${newLen} 个权限组`
    }

    case 'CREATE':
    case 'CREATE_ASSET':
      return `资产编码: ${row.target} | 类别已记录系统`
    
    case 'UPDATE':
    case 'UPDATE_ASSET': {
      const keys = Object.keys(details).filter(k => k !== 'updated_at')
      if (keys.length > 0) {
        const changes = keys.map(k => {
          const chineseKey = assetFieldMap[k] || k;
          const val = details[k];
          if (val && typeof val === 'object' && ('old' in val || 'new' in val)) {
            return `${chineseKey}: [旧]${val.old} -> [新]${val.new}`;
          }
          return chineseKey;
        })
        return `修改了 ${keys.length} 项属性: ${changes.join('; ')}`
      }
      return '修改了资产属性完成'
    }

    case 'BATCH_DELETE_HARD':
      return `共彻底删除了 ${details.ids?.length || row.target.replace('数量: ', '')} 台设备的全部底层数据记录`

    case 'IMPORT_EXCEL': {
      const success = row.target?.match(/成功:(\d+)/)?.[1] || '-'
      const failed = row.target?.match(/失败:(\d+)/)?.[1] || '0'
      return `Excel 导入完成 (成功: ${success}, 失败: ${failed})${failed !== '0' ? '，详情见悬浮窗' : ''}`
    }

    case 'UPDATE_SETTINGS':
      return '管理员更新了全局系统参数配置'

    case 'STOCK_CHECK':
      return '通过扫码完成了一次实物盘点核对'

    default:
      return Object.entries(details)
        .map(([k, v]) => `${assetFieldMap[k] || k}: ${v}`)
        .join('; ')
  }
}

// 监听路由变化，切换模块时重新加载
watch(() => currentModule.value, (newVal) => {
  queryParams.module = newVal
  queryParams.page = 1
  fetchLogs()
})

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
:deep(.el-table__row) {
  transition: all 0.3s;
}
:deep(.el-table__row:hover) {
  background-color: #f1f5f9 !important;
}
</style>
