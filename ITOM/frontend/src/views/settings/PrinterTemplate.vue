<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">标签打印模板配置</h1>
      <el-button type="primary" :loading="saving" @click="saveTemplate">
        <el-icon class="mr-1"><Check /></el-icon>
        保存打印模板
      </el-button>
    </div>

    <!-- 基础设置 -->
    <el-card shadow="never" class="border-gray-100 mb-6">
      <template #header>
        <div class="font-bold text-gray-700">全局纸张设置</div>
      </template>
      <el-form :inline="true" :model="template.paper" class="flex flex-wrap gap-4" v-loading="loading">
        <el-form-item label="纸张宽度 (mm)" class="mb-0">
          <el-input-number v-model="template.paper.width" :min="10" :max="200" />
        </el-form-item>
        <el-form-item label="纸张高度 (mm)" class="mb-0">
          <el-input-number v-model="template.paper.height" :min="10" :max="200" />
        </el-form-item>
        <el-form-item label="打印方向" class="mb-0">
          <el-select v-model="template.paper.orientation" style="width: 120px">
            <el-option label="正常 (0°)" :value="0" />
            <el-option label="横向 (90°)" :value="90" />
            <el-option label="翻转 (180°)" :value="180" />
            <el-option label="倒置 (270°)" :value="270" />
          </el-select>
        </el-form-item>
        <el-form-item label="纸张类型" class="mb-0">
          <el-select v-model="template.paper.gapType" style="width: 120px">
            <el-option label="连续纸 (0)" :value="0" />
            <el-option label="间隙纸 (2)" :value="2" />
            <el-option label="黑标纸 (3)" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="打印浓度 (0-14)" class="mb-0">
          <el-input-number v-model="template.paper.darkness" :min="0" :max="14" />
        </el-form-item>
        <el-form-item label="打印速度 (0-4)" class="mb-0">
          <el-input-number v-model="template.paper.speed" :min="0" :max="4" />
        </el-form-item>
      </el-form>
      <div class="text-xs text-gray-400 mt-4">
        提示：常见的固定资产标签纸为宽 70mm、高 50mm 间隙纸。
      </div>
    </el-card>

    <!-- 动态配置与实时预览 -->
    <el-row :gutter="20" class="items-start">
      <el-col :span="16">
        <el-card shadow="never" class="border-gray-100">
          <template #header>
        <div class="flex justify-between items-center">
          <div class="font-bold text-gray-700">模板内容元素</div>
          <div>
            <el-button type="warning" plain size="small" @click="loadFourRowTemplate">
              <el-icon><Grid /></el-icon> 导入(图一)四行带码模板
            </el-button>
            <el-button type="warning" plain size="small" @click="loadTableTemplate">
              <el-icon><Grid /></el-icon> 导入(旧版)六行模板
            </el-button>
            <el-button type="success" plain size="small" style="margin-left:8px" @click="addTextElement">
              <el-icon><Plus /></el-icon> 文本
            </el-button>
            <el-button type="primary" plain size="small" @click="addQrcodeElement">
              <el-icon><CopyDocument /></el-icon> 二维码
            </el-button>
            <el-button type="info" plain size="small" @click="addLineElement">
              <el-icon><Minus /></el-icon> 横线
            </el-button>
            <el-button type="info" plain size="small" @click="addVLineElement">
              <el-icon><Minus style="transform: rotate(90deg)" /></el-icon> 竖线
            </el-button>
            <el-button type="info" plain size="small" @click="addRectElement">
              <el-icon><FullScreen /></el-icon> 矩形 
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="template.elements" style="width: 100%" v-loading="loading" border>
        <el-table-column label="元素类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'qrcode' ? 'success' : (row.type === 'line' || row.type === 'rect' ? 'info' : 'primary')" effect="light">
              {{ row.type === 'qrcode' ? '二维码' : (row.type === 'line' ? '线条' : (row.type === 'rect' ? '矩形框' : '文字(动态)')) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="位置 X/Y (mm)" width="160">
          <template #default="{ row }">
            <div class="flex items-center space-x-2">
              <el-input-number v-model="row.x" :min="0" :step="1" size="small" controls-position="right" style="width: 65px" />
              <span class="text-gray-400">,</span>
              <el-input-number v-model="row.y" :min="0" :step="1" size="small" controls-position="right" style="width: 65px" />
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="大小 W/H (mm)" width="160">
          <template #default="{ row }">
            <div class="flex items-center space-x-2">
              <el-input-number v-model="row.width" :min="0" :step="1" size="small" controls-position="right" style="width: 65px" />
              <span class="text-gray-400" v-if="row.type !== 'qrcode'">,</span>
              <el-input-number v-model="row.height" :min="0" :step="1" size="small" controls-position="right" style="width: 65px" v-if="row.type !== 'qrcode'" />
            </div>
          </template>
        </el-table-column>

        <el-table-column label="字号/线宽(H/LW)" width="125">
          <template #default="{ row }">
            <el-input-number v-model="row.fontHeight" :min="1" :step="0.5" size="small" controls-position="right" style="width: 90px" v-if="row.type === 'text'" />
            <el-input-number v-model="row.lineWidth" :min="0.1" :step="0.1" size="small" controls-position="right" style="width: 90px" v-else-if="row.type === 'line' || row.type === 'rect'" />
            <span v-else class="text-gray-300">-</span>
          </template>
        </el-table-column>

        <el-table-column label="文本前缀 (选填)">
          <template #default="{ row }">
            <el-input v-model="row.prefix" v-if="row.type === 'text'" placeholder="如: 资产名称: " size="small" />
            <span v-else class="text-gray-300">-</span>
          </template>
        </el-table-column>

        <el-table-column label="动态映射字段 / 固定值">
          <template #default="{ row }">
            <el-input v-model="row.field" v-if="row.type !== 'text' || !row.value" placeholder="如: category.name" size="small" class="mb-1">
               <template #prepend v-if="row.type === 'qrcode'">URL</template>
            </el-input>
            <el-input v-model="row.value" v-if="row.type === 'text' && !row.field" placeholder="如果是固定文本 (如公司名)" size="small">
              <template #prepend>固定</template>
            </el-input>
            <div class="text-[10px] text-gray-400 mt-1" v-if="row.type === 'text'">
              <span class="cursor-pointer hover:text-primary" @click="row.field=''; row.value='公司名称'">设为固定值</span> | 
              <span class="cursor-pointer hover:text-primary" @click="row.field='asset_code'; row.value=''">设为动态字段</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" align="center">
          <template #default="{ $index }">
            <el-button type="danger" circle size="small" @click="removeElement($index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div class="text-sm font-bold text-gray-700 mb-2">常用映射字段参考：</div>
        <div class="flex flex-wrap gap-2 text-xs">
          <el-tag size="small" type="info">asset_code (资产编码)</el-tag>
          <el-tag size="small" type="info">category.name (分类名称)</el-tag>
          <el-tag size="small" type="info">status (状态)</el-tag>
          <el-tag size="small" type="info">user.name (保管人)</el-tag>
          <el-tag size="small" type="info">brand_model (品牌型号)</el-tag>
          <el-tag size="small" type="info">dynamic_attributes.XXX (任意动态属性)</el-tag>
        </div>
      </div>
    </el-card>
    </el-col>
    
    <el-col :span="8">
      <el-card shadow="never" class="border-gray-100 sticky top-6">
        <template #header>
          <div class="font-bold text-gray-700">实时预览 (按比例缩放)</div>
        </template>
        
        <div class="flex justify-center items-center bg-gray-100 p-8 rounded overflow-auto" style="min-height: 350px;">
          <!-- 使用 SVG 精确模拟标签纸与绘图 API -->
          <svg 
            class="bg-white relative shadow-sm transition-transform duration-500"
            :width="template.paper.width * previewScale"
            :height="template.paper.height * previewScale"
            :style="{
              transform: `rotate(${template.paper.orientation || 0}deg)`,
              transformOrigin: 'center center',
              margin: 'auto'
            }"
          >
             <g v-for="(item, idx) in template.elements" :key="idx" class="cursor-pointer hover:opacity-80 transition-opacity">
               
                <!-- 矩形渲染 -->
                <rect v-if="item.type === 'rect'"
                   :x="item.x * previewScale"
                   :y="item.y * previewScale"
                   :width="Math.max(item.width * previewScale, 0)"
                   :height="Math.max(item.height * previewScale, 0)"
                   fill="none"
                   stroke="black"
                   :stroke-width="(item.lineWidth || 0.5) * previewScale"
                />
                
                <!-- 线条渲染 -->
                <line v-if="item.type === 'line'"
                   :x1="item.x * previewScale"
                   :y1="item.y * previewScale"
                   :x2="(item.x + (item.width || 0)) * previewScale"
                   :y2="(item.y + (item.height || 0)) * previewScale"
                   stroke="black"
                   :stroke-width="(item.lineWidth || 0.5) * previewScale"
                />

                <!-- 文本渲染 -->
                <text v-if="item.type === 'text'"
                   :x="item.x * previewScale"
                   :y="(item.y + item.fontHeight) * previewScale"
                   :font-size="item.fontHeight * previewScale"
                   font-family="monospace, sans-serif"
                   font-weight="bold"
                   fill="black"
                   style="dominant-baseline: alphabetic;"
                >{{ item.prefix || '' }}{{ item.value || (item.field ? `[${item.field}]` : '文本') }}</text>
                
                <!-- 二维码渲染 -->
                <foreignObject v-if="item.type === 'qrcode'"
                   :x="item.x * previewScale"
                   :y="item.y * previewScale"
                   :width="item.width * previewScale"
                   :height="item.width * previewScale"
                >
                  <div class="w-[100%] h-[100%] bg-black flex items-center justify-center text-white" style="opacity: 0.8">
                    <el-icon :size="item.width * previewScale / 2 + 'px'"><Grid /></el-icon>
                  </div>
                </foreignObject>
             </g>
          </svg>
        </div>
        <div class="mt-3 text-xs text-gray-400 text-center">
          当前纸张设置: {{ template.paper.width }}mm x {{ template.paper.height }}mm
        </div>
      </el-card>
    </el-col>
  </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Check, Delete, Plus, CopyDocument, Grid } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const loading = ref(false)
const saving = ref(false)

// 模板数据结构
const template = ref({
  paper: {
    width: 70,
    height: 50,
    orientation: 0,
    gapType: 2,
    darkness: 8,
    speed: 2
  },
  elements: [] as any[]
})

// 默认兜底配置
const defaultElements = [
  { type: 'text', value: '先惠自动化技术有限公司', x: 5, y: 5, fontHeight: 3, width: 42, height: 6 },
  { type: 'text', field: 'asset_code', prefix: '资产编码: ', x: 5, y: 13, fontHeight: 3, width: 42, height: 6 },
  { type: 'text', field: 'category.name', prefix: '名称: ', x: 5, y: 21, fontHeight: 3, width: 42, height: 6 },
  { type: 'text', field: 'dynamic_attributes.规格型号', prefix: '型号: ', x: 5, y: 29, fontHeight: 3, width: 42, height: 6 },
  { type: 'qrcode', field: 'qr_code_token', x: 50, y: 10, width: 18 }
]

const fetchData = async () => {
  loading.value = true
  try {
    const { data: config } = await axios.get('/api/settings/')
    if (config.PRINT_TEMPLATE && config.PRINT_TEMPLATE.paper && config.PRINT_TEMPLATE.elements) {
      // 使用已存储的新版模板
      template.value = config.PRINT_TEMPLATE
    } else {
      // 没有或者只有旧版 config（包含 rows, fonts），采用新的兜底格式
      template.value.elements = [...defaultElements]
    }
  } catch (err: any) {
    ElMessage.error('获取打印模板失败: ' + (err.response?.data?.detail || err.message))
    template.value.elements = [...defaultElements]
  } finally {
    loading.value = false
  }
}

const saveTemplate = async () => {
  saving.value = true
  try {
    const payload = {
      print_template: template.value
    }
    const { data } = await axios.post('/api/settings/', payload)
    if (data.success) {
      ElMessage.success('打印模板保存成功，请在移动端重新打卡打印测试')
    }
  } catch (err: any) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

const addTextElement = () => {
  template.value.elements.push({
    type: 'text',
    field: '',
    value: '',
    prefix: '',
    x: 5,
    y: 10,
    fontHeight: 3,
    width: 40,
    height: 6
  })
}

const addQrcodeElement = () => {
  template.value.elements.push({
    type: 'qrcode',
    field: 'qr_code_token',
    x: 50,
    y: 10,
    width: 18
  })
}

const addLineElement = () => {
  template.value.elements.push({
    type: 'line', x: 2, y: 10, width: 40, height: 0, lineWidth: 0.5
  })
}

const addVLineElement = () => {
  template.value.elements.push({
    type: 'line', x: 10, y: 2, width: 0, height: 40, lineWidth: 0.5
  })
}

const addRectElement = () => {
  template.value.elements.push({
    type: 'rect', x: 2, y: 2, width: 66, height: 46, lineWidth: 0.5
  })
}

const loadFourRowTemplate = () => {
  template.value.paper = { width: 70, height: 50, orientation: 0, gapType: 2, darkness: 8, speed: 2 };
  template.value.elements = [
    { type: 'rect', x: 2, y: 2, width: 66, height: 46, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 12, width: 66, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 24, width: 44, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 36, width: 44, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 46, y: 12, width: 0, height: 36, lineWidth: 0.5 },
    { type: 'text', value: '先惠自动化技术(武汉)有限责任公司', x: 4, y: 5, fontHeight: 4, width: 62, height: 6 },
    { type: 'text', field: 'asset_code', prefix: '资产编码: ', x: 4, y: 16, fontHeight: 3.5, width: 40, height: 6 },
    { type: 'text', field: 'category.name', prefix: '名称: ', x: 4, y: 28, fontHeight: 3.5, width: 40, height: 6 },
    { type: 'text', field: 'dynamic_attributes.规格型号', prefix: '型号: ', x: 4, y: 40, fontHeight: 3.5, width: 40, height: 6 },
    { type: 'qrcode', field: 'qr_code_token', x: 49, y: 17, width: 17 }
  ];
  ElMessage.success('已自动载入图一等比四行模板，请调整使用')
}

const loadTableTemplate = () => {
  template.value.paper = { width: 70, height: 50, orientation: 0, gapType: 2, darkness: 8, speed: 2 };
  template.value.elements = [
    { type: 'rect', x: 2, y: 2, width: 66, height: 46, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 10, width: 66, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 18, width: 66, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 26, width: 66, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 34, width: 66, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 2, y: 41, width: 50, height: 0, lineWidth: 0.5 },
    { type: 'line', x: 52, y: 34, width: 0, height: 14, lineWidth: 0.5 },
    { type: 'text', value: '先惠自动化技术(武汉)有限责任公司', x: 4, y: 4, fontHeight: 4, width: 62, height: 6 },
    { type: 'text', field: 'asset_code', prefix: '资产编码: ', x: 4, y: 12, fontHeight: 3.5, width: 62, height: 6 },
    { type: 'text', field: 'category.name', prefix: '资产名称: ', x: 4, y: 20, fontHeight: 3.5, width: 62, height: 6 },
    { type: 'text', field: 'dynamic_attributes.规格型号', prefix: '资产型号: ', x: 4, y: 28, fontHeight: 3.5, width: 62, height: 6 },
    { type: 'text', field: 'dynamic_attributes.序列号', prefix: '序 列 号 : ', x: 4, y: 36, fontHeight: 3, width: 46, height: 5 },
    { type: 'text', field: 'dynamic_attributes.使用日期', prefix: '使用日期: ', x: 4, y: 43, fontHeight: 3, width: 46, height: 5 },
    { type: 'qrcode', field: 'qr_code_token', x: 53, y: 35, width: 13 }
  ];
  ElMessage.success('已自动载入预制表格模板')
}

const removeElement = (index: number) => {
  template.value.elements.splice(index, 1)
}

// 预览缩放比例，1mm = 4.5px
const previewScale = 4.5;

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* 隐藏数字输入框的双箭头 以节约空间 */
:deep(.el-input-number.is-controls-right .el-input__wrapper) {
  padding-left: 8px;
  padding-right: 32px;
}
</style>
