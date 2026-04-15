<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800 tracking-tight">账号与权限分配</h1>
        <p class="text-sm text-gray-500 mt-1">管理归属地管理员账号及系统角色权限 (仅集团超管可操作)</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        分配新账号
      </el-button>
    </div>

    <!-- 用户列表 -->
    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="登录名" width="150">
          <template #default="{ row }">
            <span class="font-medium text-gray-800">{{ row.username }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="联系邮箱" min-width="180" />
        <el-table-column prop="role" label="系统角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" effect="plain">
              {{ row.role === 'admin' ? '系统管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location_name" label="负责归属地" width="160">
          <template #default="{ row }">
            <el-tag v-if="row.is_group_admin" type="danger" effect="dark">集团超级管理员</el-tag>
            <el-tag v-else-if="row.location_id" type="warning" effect="plain">{{ row.location_name }}</el-tag>
            <span v-else class="text-gray-400 text-sm">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="账号状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <template v-if="row.username !== 'admin'">
              <el-button link type="primary" :icon="Edit" @click="openEditDialog(row)">设置</el-button>
              <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
            </template>
            <span v-else class="text-gray-400 text-xs">系统内建禁止操作</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 账号分配表单 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingUser ? '编辑账号与权限' : '分配新管理员账号'"
      width="500px"
      class="rounded-2xl"
    >
      <el-form :model="formData" label-position="top" ref="formRef" :rules="formRules">
        <el-form-item label="登录名 (用户名)" prop="username">
          <el-select
            v-if="!editingUser"
            v-model="formData.username"
            filterable
            remote
            reserve-keyword
            allow-create
            default-first-option
            placeholder="搜索姓名或域账号拼音..."
            :remote-method="searchAdUsers"
            :loading="adLoading"
            class="w-full"
            @change="handleUserSelect"
          >
            <el-option
              v-for="u in adUsersOptions"
              :key="u.username"
              :label="`${u.display_name} (${u.username})`"
              :value="u.username"
            >
              <div class="flex justify-between items-center">
                <span>{{ u.display_name }}</span>
                <span class="text-xs text-gray-400">{{ u.username }}</span>
              </div>
            </el-option>
          </el-select>
          <el-input v-else v-model="formData.username" disabled />
        </el-form-item>

        <el-form-item :label="editingUser ? '登录密码 (留空则不修改)' : '初始密码'" :prop="editingUser ? '' : 'password'">
          <el-input v-model="formData.password" placeholder="请输入密码" show-password />
        </el-form-item>

        <el-form-item label="负责归属地" prop="location_id">
          <el-select v-model="formData.location_id" placeholder="选择账号管理的归属地范围" class="w-full" clearable>
            <el-option v-for="loc in locationList" :key="loc.id" :label="loc.name" :value="loc.id" />
          </el-select>
          <div class="text-xs text-gray-400 mt-1">选定归属地后，该账号登录仅可见此地的资产；未分配则表示看全体</div>
        </el-form-item>

        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="系统角色" prop="role">
            <el-select v-model="formData.role">
              <el-option label="系统管理员" value="admin" />
              <el-option label="普通用户" value="user" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="账号状态" prop="is_active" v-if="editingUser">
            <el-switch v-model="formData.is_active" active-text="正常畅通" inactive-text="禁止登录" />
          </el-form-item>
        </div>

        <el-form-item label="联系邮箱">
          <el-input v-model="formData.email" placeholder="重置密码等通知 (选填)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">
            {{ editingUser ? '保存设置' : '确认分配' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'

const users = ref<any[]>([])
const locationList = ref<any[]>([])
const loading = ref(false)

const adLoading = ref(false)
const adUsersOptions = ref<any[]>([])

const dialogVisible = ref(false)
const saving = ref(false)
const editingUser = ref<any>(null)
const formRef = ref<FormInstance>()

const formData = reactive({
  username: '',
  password: '',
  email: '',
  role: 'admin',
  location_id: '' as any,
  is_active: true
})

const formRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入登录用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入由字母/数字组成的密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'blur' }]
})

const fetchLocations = async () => {
    try {
        const { data } = await axios.get('/api/locations/')
        locationList.value = data
    } catch {
        // ...
    }
}

const fetchUsers = async () => {
    loading.value = true
    try {
        const { data } = await axios.get('/api/users/')
        users.value = data
    } catch (err: any) {
        if (err.response?.status === 403) {
            ElMessage.error('权限不足：仅集团超管可管理账号分发')
        } else {
            ElMessage.error('无法拉取账号列表')
        }
    } finally {
        loading.value = false
    }
}

const searchAdUsers = async (query: string) => {
    if (query) {
        adLoading.value = true
        try {
            // 直接搜索 AD 域用户
            const { data } = await axios.get('/api/ad/users', { params: { keyword: query } })
            adUsersOptions.value = data.users || []
        } catch {
            adUsersOptions.value = []
        } finally {
            adLoading.value = false
        }
    } else {
        adUsersOptions.value = []
    }
}

const handleUserSelect = (val: string) => {
    // 根据选择自动填充邮箱
    const selected = adUsersOptions.value.find(u => u.username === val)
    if (selected && selected.email) {
        formData.email = selected.email
    }
}

const openCreateDialog = () => {
    editingUser.value = null
    formData.username = ''
    formData.password = ''
    formData.email = ''
    formData.role = 'admin'
    formData.location_id = ''
    formData.is_active = true
    dialogVisible.value = true
}

const openEditDialog = (row: any) => {
    editingUser.value = row
    formData.username = row.username
    formData.password = ''
    formData.email = row.email || ''
    formData.role = row.role
    formData.location_id = row.location_id || ''
    formData.is_active = row.is_active
    dialogVisible.value = true
}

const handleDelete = (row: any) => {
    ElMessageBox.confirm(`确定要删除账号「${row.username}」吗？操作不可恢复！`, '危险预警', {
        confirmButtonText: '强制删除',
        cancelButtonText: '手滑了',
        type: 'error'
    }).then(async () => {
        try {
            await axios.delete(`/api/users/${row.id}`)
            ElMessage.success('账号已删除')
            fetchUsers()
        } catch (err: any) {
            ElMessage.error(err.response?.data?.detail || '删除失败')
        }
    }).catch(() => {})
}

const submitForm = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
        if (!valid) return
        saving.value = true
        try {
            const payload = { ...formData }
            // 对空字符串转null处理
            if (payload.location_id === '') {
                payload.location_id = null
            }
            
            if (editingUser.value) {
                // 不传空密码
                if (!payload.password) {
                    delete (payload as any).password
                }
                await axios.put(`/api/users/${editingUser.value.id}`, payload)
                ElMessage.success('账号权限已同步')
            } else {
                await axios.post('/api/users/', payload)
                ElMessage.success('账号分配成功')
            }
            dialogVisible.value = false
            fetchUsers()
        } catch (err: any) {
            ElMessage.error(err.response?.data?.detail || '分配归属地账号失败')
        } finally {
            saving.value = false
        }
    })
}

onMounted(() => {
    fetchLocations()
    fetchUsers()
})
</script>
