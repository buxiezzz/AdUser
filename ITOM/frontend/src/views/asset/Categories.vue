<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">资产分类字典</h1>
      <el-button type="primary" @click="handleCreate">新增资产类别</el-button>
    </div>

    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <el-table :data="categories" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="业务类型名称" width="200" />
        <el-table-column label="包含的特有属性 (JSONB)">
          <template #default="{ row }">
            <el-tag v-for="(type, key) in row.default_attributes" :key="key" class="mr-2 mb-1" size="small">
              {{ key }}: {{ type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑修改
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isNew ? '新增业务分类' : '修改业务分类'" width="500px">
      <el-form label-position="top">
        <el-form-item label="分类名称" required>
          <el-input v-model="form.name" placeholder="如: 笔记本、服务器、移动设备" />
        </el-form-item>
        <el-form-item label="动态属性模板 (JSON)">
          <el-input v-model="form.default_attributes_str" type="textarea" rows="4" placeholder='例如: {"CPU": "string", "内存": "string", "MAC地址": "string"}' />
          <div class="text-xs text-gray-400 mt-1">请填写标准的 JSON 字典，以便在该分类下的资产强制具备这些属性。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitSave" :loading="submitLoading">保存入库</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const categories = ref<any[]>([])

const fetchCategories = async () => {
    loading.value = true
    try {
        const { data } = await axios.get('/api/assets/categories')
        categories.value = data || []
    } catch {
        ElMessage.error('无法拉取分类数据')
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchCategories()
})

const dialogVisible = ref(false)
const submitLoading = ref(false)
const isNew = ref(true)
const currentCategoryId = ref<number | null>(null)

const form = ref({
    name: '',
    default_attributes_str: '{\n  \n}'
})

const handleCreate = () => {
    isNew.value = true
    currentCategoryId.value = null
    form.value = { name: '', default_attributes_str: '{\n  \n}' }
    dialogVisible.value = true
}

const handleEdit = (row: any) => {
    isNew.value = false
    currentCategoryId.value = row.id
    form.value = { 
        name: row.name, 
        default_attributes_str: JSON.stringify(row.default_attributes, null, 2)
    }
    dialogVisible.value = true
}

const submitSave = async () => {
    if (!form.value.name) return ElMessage.warning('分类名不能为空')
    let defaultAttrs = {}
    try {
        defaultAttrs = JSON.parse(form.value.default_attributes_str)
    } catch {
        return ElMessage.warning('JSON 格式不合法')
    }
    
    submitLoading.value = true
    try {
        if (isNew.value) {
            await axios.post('/api/assets/categories', {
                name: form.value.name,
                default_attributes: defaultAttrs
            })
            ElMessage.success('分类创建成功')
        } else {
            await axios.put(`/api/assets/categories/${currentCategoryId.value}`, {
                name: form.value.name,
                default_attributes: defaultAttrs
            })
            ElMessage.success('分类修改成功')
        }
        dialogVisible.value = false
        fetchCategories()
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '保存分类失败')
    } finally {
        submitLoading.value = false
    }
}
const handleDelete = async (row: any) => {
    try {
        await ElMessageBox.confirm(`确定要删除资产类别 "${row.name}" 吗？如果有资产正属于此分类，将无法删除。`, '删除提示', {
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
        })
    } catch { return }

    loading.value = true
    try {
        await axios.delete(`/api/assets/categories/${row.id}`)
        ElMessage.success('资产分类已删除')
        fetchCategories()
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '删除失败，该分类下可能还有资产数据')
    } finally {
        loading.value = false
    }
}
</script>
