<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">IT 资产台账与全生命周期管控</h1>
      <el-button type="primary" :icon="Plus" @click="openCreateDrawer">资产录入登记</el-button>
    </div>

    <!-- 顶层汇总状态卡片 / 过滤器 -->
    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <div class="flex flex-wrap gap-4 mb-6">
        <el-input v-model="searchKeyword" placeholder="检索资产编号、品牌、或使用者姓名..." prefix-icon="Search" class="w-80" clearable />
        <el-select v-model="searchStatus" placeholder="按资产状态筛选" clearable class="w-40" >
          <el-option label="在库" value="在库" />
          <el-option label="借用中" value="借用中" />
          <el-option label="维修中" value="维修中" />
          <el-option label="已报废" value="已归档/报废" />
        </el-select>
        <el-select v-model="searchCategory" placeholder="按设备分类筛选" clearable class="w-40" >
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button @click="fetchAssets" :icon="Refresh">刷新台账</el-button>
        <el-button @click="downloadTemplate" :icon="Download" plain>下载导入模板</el-button>
        <el-upload
          action="/api/assets/import"
          :show-file-list="false"
          :before-upload="beforeUpload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          accept=".xlsx,.xls"
          :headers="uploadHeaders"
          class="inline-block flex-shrink-0"
        >
          <el-button type="success" plain :loading="uploading">一键导入资产</el-button>
        </el-upload>
        <el-button type="success" :icon="Download" @click="exportExcel">导出台账(Excel)</el-button>
        <el-button type="primary" plain :icon="Printer" :disabled="selectedAssets.length === 0" @click="printBatchLabels()">批量打印标签 ({{ selectedAssets.length }})</el-button>
      </div>

      <el-table :data="filteredAssets" style="width: 100%" v-loading="loading" border stripe @selection-change="handleSelectionChange">
         <el-table-column type="selection" width="55" fixed="left" />
         <el-table-column label="资产状态" width="100">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column prop="asset_code" label="资产编码" width="160">
            <template #default="{ row }">
              <span class="font-mono font-medium text-indigo-700">{{ row.asset_code || '未分配编号' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="资产名称" width="120">
           <template #default="{ row }">
             <el-tag size="small" type="info">{{ getCategoryName(row.category_id) }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="规格型号" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="text-gray-600">{{ row.dynamic_attributes ? row.dynamic_attributes['规格型号'] : '' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="计量单位" width="100">
            <template #default="{ row }">
              <span class="text-gray-600">{{ row.dynamic_attributes && row.dynamic_attributes['计量单位'] ? row.dynamic_attributes['计量单位'] : '台/件' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="入库日期" width="160">
            <template #default="{ row }">
              <span class="text-gray-600 text-sm">{{ new Date(row.created_at).toLocaleDateString() }}</span>
            </template>
         </el-table-column>
         <el-table-column label="所属组织" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="text-gray-600">{{ row.owner ? row.owner.department : (row.dynamic_attributes ? row.dynamic_attributes['所属组织'] : '-') }}</span>
            </template>
         </el-table-column>
         <el-table-column label="使用人" width="150" show-overflow-tooltip>
           <template #default="{ row }">
             <div v-if="row.owner" class="flex items-center space-x-2">
                <el-avatar size="small" class="bg-indigo-100 text-indigo-800">{{ row.owner.name.charAt(0) }}</el-avatar>
                <div class="flex flex-col">
                  <span class="text-sm font-medium leading-none">{{ row.owner.name }}</span>
                </div>
             </div>
             <span v-else class="text-gray-400 text-sm">-</span>
           </template>
         </el-table-column>
         <el-table-column label="序列号" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="text-gray-600 font-mono">{{ row.dynamic_attributes ? row.dynamic_attributes['序列号'] : '' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="备注" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="text-gray-600">{{ row.dynamic_attributes ? row.dynamic_attributes['备注'] : '' }}</span>
            </template>
         </el-table-column>
         <el-table-column 
            v-for="key in dynamicHeaders" 
            :key="key" 
            :label="key"
            min-width="120"
            show-overflow-tooltip
          >
            <template #default="{ row }">
               <span class="text-gray-600">{{ row.dynamic_attributes ? row.dynamic_attributes[key] : '' }}</span>
            </template>
         </el-table-column>
         <el-table-column label="操作管控" width="200" fixed="right">
           <template #default="{ row }">
             <el-button link type="primary" size="small" @click="openManageDrawer(row)">
               管理/调拨
             </el-button>
             <el-button link type="success" size="small" @click="printBatchLabels([row])">
               打印标签
             </el-button>
             <el-button link type="info" size="small" @click="openLogs(row)">
               追溯日志
             </el-button>
           </template>
         </el-table-column>
      </el-table>
    </el-card>

    <!-- 侧边栏资产抽屉(新建/维护) -->
    <el-drawer
      v-model="drawerVisible"
      :title="isNew ? '新资产入库登记' : `资产档案与流转: ${currentAsset?.asset_code || '未命名'}`"
      size="650px"
      append-to-body
      destroy-on-close
    >
      <div v-loading="submitLoading" class="px-4 pb-12">
        <el-form label-position="top">
          <!-- 基础信息 -->
          <div class="grid grid-cols-2 gap-4">
            <el-form-item label="资产状态" required>
              <el-select v-model="form.status" placeholder="流转状态" @change="handleStatusChange">
                <el-option label="在库" value="在库" />
                <el-option label="借用中" value="借用中" />
                <el-option label="维修中" value="维修中" />
                <el-option label="已归档/报废" value="已归档/报废" />
              </el-select>
            </el-form-item>
            <el-form-item label="资产编码" required>
              <el-input v-model="form.asset_code" placeholder="如 IT-PC-2023001" />
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="资产分类" required>
              <el-select v-model="form.category_id" placeholder="选择资产类型" @change="handleCategoryChange">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="规格型号">
               <el-input v-model="form.dynamic_attributes['规格型号']" placeholder="如: ThinkPad T14" />
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="计量单位">
               <el-input v-model="form.dynamic_attributes['计量单位']" placeholder="如: 台/件" />
            </el-form-item>
            <el-form-item label="入库日期">
               <el-date-picker v-if="!isNew" v-model="form.created_at" type="datetime" disabled class="w-full" />
               <el-input v-else placeholder="保存后系统自动生成" disabled />
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="所属组织">
               <el-input v-model="form.dynamic_attributes['所属组织']" placeholder="如未使用人绑定，可手动指定" />
            </el-form-item>
            <el-form-item label="使用人" class="flex-1">
              <el-select
                v-model="form.owner_id"
                filterable
                remote
                clearable
                placeholder="键入检索 AD/本地员工"
                :remote-method="searchEmployees"
                :loading="empLoading"
                :disabled="form.status === '在库' || form.status === '已归档/报废'"
              >
                <el-option
                  v-for="emp in employees"
                  :key="emp.id"
                  :label="`${emp.name} (${emp.ad_account || '本地'})`"
                  :value="emp.id"
                >
                  <span style="float: left">{{ emp.name }}</span>
                  <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">{{ emp.department }}</span>
                </el-option>
              </el-select>
              <div v-if="form.status === '在库' || form.status === '已归档/报废'" class="text-xs text-gray-400 mt-1">在库或报废状态下不可绑定人。</div>
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="序列号">
               <el-input v-model="form.dynamic_attributes['序列号']" placeholder="硬件SN码..." />
            </el-form-item>
            <el-form-item label="备注">
               <el-input v-model="form.dynamic_attributes['备注']" type="textarea" rows="1" placeholder="补充说明..." />
            </el-form-item>
          </div>

          <el-divider>其他附加业务扩展属性</el-divider>
          
          <div v-if="Object.keys(currentCatTpl).filter(k => !['规格型号','计量单位','所属组织','序列号','备注'].includes(String(k))).length > 0" class="bg-gray-50 border rounded-lg p-4 space-y-4">
            <el-form-item 
              v-for="(typeDesc, key) in currentCatTpl" 
              :key="key" 
              v-show="!['规格型号','计量单位','所属组织','序列号','备注'].includes(String(key))"
              :label="`${key} ${typeDesc ? '('+typeDesc+')' : ''}`"
            >
               <el-input v-model="form.dynamic_attributes[key]" :placeholder="`输入${key}`" />
            </el-form-item>
          </div>
          <div v-else class="text-sm text-gray-400 text-center py-4 bg-gray-50 rounded-lg">
            暂无需要填写的其他附加模板属性。
          </div>

          <div class="mt-8 flex justify-end space-x-3">
            <el-button @click="drawerVisible = false">取消放弃</el-button>
            <el-button type="danger" plain v-if="!isNew && form.status !== '已归档/报废'" @click="doArchive">报废与归档</el-button>
            <el-button type="danger" v-if="!isNew" @click="doHardDelete">彻底删除台账</el-button>
            <el-button type="primary" @click="submitSave">保存提交台账</el-button>
          </div>
        </el-form>
      </div>
    </el-drawer>

    <!-- 隐藏的渲染区域，用于生成含有二维码的DOM给打印机 -->
    <div id="batch-print-area" style="position: absolute; left: -9999px; top: -9999px; width: 70mm; opacity: 0; pointer-events: none;">
      <div v-for="asset in assetsToPrint" :key="asset.id" class="print-label-page" :style="{ width: printConfig.width + 'mm', height: printConfig.height + 'mm', boxSizing: 'border-box', padding: printConfig.padding + 'mm', pageBreakAfter: 'always', display: 'flex', flexDirection: 'column', background: 'white', color: 'black', fontFamily: '\'Helvetica Neue\', Helvetica, Arial, sans-serif', overflow: 'hidden' }">
        <table :style="{ width: '100%', height: '100%', borderCollapse: 'collapse', border: printConfig.border + 'px solid black', fontWeight: 'bold', tableLayout: 'fixed' }">
          <colgroup>
            <col style="width: auto;" />
            <col :style="{ width: (printConfig.qrSize + 4) + 'px' }" />
          </colgroup>
          <tr>
            <td colspan="2" :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r1 + 'mm', padding: 0, textAlign: 'center', fontSize: printConfig.fonts.title + 'px', fontWeight: 900, letterSpacing: '-0.5px', whiteSpace: 'nowrap', overflow: 'hidden' }">先惠自动化技术(武汉)有限责任公司</td>
          </tr>
          <tr>
            <td colspan="2" :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r2 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.code + 'px', whiteSpace: 'nowrap', overflow: 'hidden' }">资产编码: {{ asset.asset_code }}</td>
          </tr>
          <tr>
            <td colspan="2" :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r3 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.name + 'px', whiteSpace: 'nowrap', overflow: 'hidden' }">资产名称: {{ getCategoryName(asset.category_id) }}</td>
          </tr>
          <tr>
            <td colspan="2" :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r4 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.spec + 'px', whiteSpace: 'nowrap', overflow: 'hidden' }">资产型号: {{ asset.dynamic_attributes?.['规格型号'] || '-' }}</td>
          </tr>
          <tr>
             <td :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r5 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.serial + 'px', borderRight: 'none', whiteSpace: 'nowrap', overflow: 'hidden' }">序 列 号 &nbsp;: {{ asset.dynamic_attributes?.['序列号'] || '-' }}</td>
             <td rowspan="2" :style="{ border: printConfig.border + 'px solid black', borderLeft: printConfig.border + 'px solid black', padding: '2px', textAlign: 'center', verticalAlign: 'middle', width: '1%' }">
                <qrcode-vue :value="getQrUrl(asset)" :size="printConfig.qrSize" level="H" render-as="svg" style="display:block; margin: 0 auto;" />
             </td>
          </tr>
          <tr>
             <td :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r6 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.date + 'px', borderRight: 'none', whiteSpace: 'nowrap', overflow: 'hidden' }">使用日期: {{ new Date(asset.created_at).toISOString().split('T')[0] }}</td>
          </tr>
        </table>
      </div>
    </div>

    <!-- WYSIWYG 可视化打印排版设计器 -->
    <el-dialog v-model="printConfigVisible" title="定制修改打印排版与实时预览" width="900px" align-center @close="stopDrag">
       <!-- 顶部全局工具栏 -->
       <div class="flex items-center gap-4 bg-gray-50 p-3 rounded mb-4 border border-gray-200">
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">纸宽(mm)</span>
           <el-input-number v-model="printConfig.width" :min="30" :max="150" size="small" style="width: 100px" />
         </div>
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">纸高(mm)</span>
           <el-input-number v-model="printConfig.height" :min="30" :max="150" size="small" style="width: 100px" />
         </div>
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">留白(mm)</span>
           <el-input-number v-model="printConfig.padding" :step="0.5" :min="0" :max="10" size="small" style="width: 100px" />
         </div>
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">边框(px)</span>
           <el-input-number v-model="printConfig.border" :min="0" :max="10" size="small" style="width: 100px" />
         </div>
         
         <el-divider direction="vertical" />

         <!-- 动态选中元素字号调节 (类似Word) -->
         <div class="flex items-center gap-2" v-if="selectedElement">
           <span class="text-sm font-bold text-blue-600">当前选中文字字号(px)</span>
           <el-input-number v-if="selectedElement === 'qr'" v-model="printConfig.qrSize" :min="10" :max="150" size="small" style="width: 100px" />
           <el-input-number v-else v-model="(printConfig.fonts as any)[selectedElement]" :min="8" :max="50" size="small" style="width: 100px" />
         </div>
         <div v-else class="text-sm text-gray-400 italic">单击表格内文字以调节字号大小...</div>
       </div>

       <!-- 居中可视化预览画板 -->
       <div class="flex items-center justify-center bg-gray-100 rounded border border-dashed border-gray-300 relative overflow-hidden" 
            style="min-height: 400px; user-select: none;" @mousedown.self="selectElement(null)">
            <span class="absolute top-2 left-2 text-xs text-gray-400 pointer-events-none">直接拖拽表格边框改变大小，单击段落修改字号。</span>
            
            <div v-if="assetsToPrint[0]" class="bg-white shadow relative origin-center scale-125 transition-all" 
                 :style="{ 
                    width: printConfig.width + 'mm', 
                    height: printConfig.height + 'mm', 
                    boxSizing: 'border-box', 
                    padding: printConfig.padding + 'mm', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    color: 'black', 
                    fontFamily: '\'Helvetica Neue\', Helvetica, Arial, sans-serif', 
                    overflow: 'hidden'
                 }"
                 @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag"
                 >
                 
              <table :style="{ 
                width: '100%', height: '100%', borderCollapse: 'collapse', 
                border: printConfig.border + 'px solid black', fontWeight: 'bold', tableLayout: 'fixed', position: 'relative' 
              }">
                <colgroup>
                  <col style="width: auto;" />
                  <col :style="{ width: (printConfig.qrSize + 4) + 'px' }" />
                </colgroup>
                <!-- Row 1 -->
                <tr>
                  <td colspan="2" 
                      @mousedown.stop="selectElement('title')"
                      :style="{ 
                        border: printConfig.border + 'px solid black', 
                        height: printConfig.rows.r1 + 'mm', 
                        padding: 0, textAlign: 'center', 
                        fontSize: printConfig.fonts.title + 'px', 
                        fontWeight: 900, letterSpacing: '-0.5px', whiteSpace: 'nowrap', overflow: 'hidden',
                        position: 'relative', outline: selectedElement === 'title' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer'
                      }">
                    先惠自动化技术(武汉)有限责任公司
                    <!-- Drag handle for row 1 bottom -->
                    <div @mousedown.stop="startDragRow($event, 'r1')" style="position:absolute; bottom:-1px; left:0; right:0; height:3px; background:rgba(0,120,250,0); z-index:10; cursor:row-resize" @mouseenter="setHandleBg($event, true)" @mouseleave="setHandleBg($event, false)"></div>
                  </td>
                </tr>
                <!-- Row 2 -->
                <tr>
                  <td colspan="2" 
                      @mousedown.stop="selectElement('code')"
                      :style="{ 
                        border: printConfig.border + 'px solid black', 
                        height: printConfig.rows.r2 + 'mm', 
                        padding: '0 2mm', fontSize: printConfig.fonts.code + 'px', whiteSpace: 'nowrap', overflow: 'hidden',
                        position: 'relative', outline: selectedElement === 'code' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer'
                      }">
                    资产编码: {{ assetsToPrint[0].asset_code }}
                    <!-- Drag handle for row 2 bottom -->
                    <div @mousedown.stop="startDragRow($event, 'r2')" style="position:absolute; bottom:-1px; left:0; right:0; height:3px; background:rgba(0,120,250,0); z-index:10; cursor:row-resize" @mouseenter="setHandleBg($event, true)" @mouseleave="setHandleBg($event, false)"></div>
                  </td>
                </tr>
                <!-- Row 3 -->
                <tr>
                  <td colspan="2" 
                      @mousedown.stop="selectElement('name')"
                      :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r3 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.name + 'px', whiteSpace: 'nowrap', overflow: 'hidden', position: 'relative', outline: selectedElement === 'name' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer' }">
                    资产名称: {{ getCategoryName(assetsToPrint[0].category_id) }}
                    <!-- Drag handle for row 3 bottom -->
                    <div @mousedown.stop="startDragRow($event, 'r3')" style="position:absolute; bottom:-1px; left:0; right:0; height:3px; background:rgba(0,120,250,0); z-index:10; cursor:row-resize" @mouseenter="setHandleBg($event, true)" @mouseleave="setHandleBg($event, false)"></div>
                  </td>
                </tr>
                <!-- Row 4 -->
                <tr>
                  <td colspan="2" 
                      @mousedown.stop="selectElement('spec')"
                      :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r4 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.spec + 'px', whiteSpace: 'nowrap', overflow: 'hidden', position: 'relative', outline: selectedElement === 'spec' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer' }">
                    资产型号: {{ assetsToPrint[0].dynamic_attributes?.['规格型号'] || '-' }}
                    <!-- Drag handle for row 4 bottom -->
                    <div @mousedown.stop="startDragRow($event, 'r4')" style="position:absolute; bottom:-1px; left:0; right:0; height:3px; background:rgba(0,120,250,0); z-index:10; cursor:row-resize" @mouseenter="setHandleBg($event, true)" @mouseleave="setHandleBg($event, false)"></div>
                  </td>
                </tr>
                <!-- Row 5 -->
                <tr>
                   <td @mousedown.stop="selectElement('serial')"
                       :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r5 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.serial + 'px', borderRight: 'none', whiteSpace: 'nowrap', overflow: 'hidden', position: 'relative', outline: selectedElement === 'serial' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer' }">
                     序 列 号 &nbsp;: {{ assetsToPrint[0].dynamic_attributes?.['序列号'] || '-' }}
                     <!-- Drag handle for row 5 bottom -->
                     <div @mousedown.stop="startDragRow($event, 'r5')" style="position:absolute; bottom:-1px; left:0; right:0; height:3px; background:rgba(0,120,250,0); z-index:10; cursor:row-resize" @mouseenter="setHandleBg($event, true)" @mouseleave="setHandleBg($event, false)"></div>
                   </td>
                   <td rowspan="2" 
                       @mousedown.stop="selectElement('qr')"
                       :style="{ border: printConfig.border + 'px solid black', borderLeft: printConfig.border + 'px solid black', padding: '2px', textAlign: 'center', verticalAlign: 'middle', width: '1%', outline: selectedElement === 'qr' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer', position: 'relative' }">
                      <qrcode-vue :value="getQrUrl(assetsToPrint[0])" :size="printConfig.qrSize" level="H" render-as="svg" style="display:block; margin: 0 auto; pointer-events: none;" />
                   </td>
                </tr>
                <!-- Row 6 -->
                <tr>
                   <td @mousedown.stop="selectElement('date')"
                       :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r6 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.date + 'px', borderRight: 'none', whiteSpace: 'nowrap', overflow: 'hidden', position: 'relative', outline: selectedElement === 'date' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer' }">
                      使用日期: {{ new Date(assetsToPrint[0].created_at).toISOString().split('T')[0] }}
                   </td>
                </tr>
              </table>
              <div v-if="isDragging" style="position:fixed; top:0; left:0; right:0; bottom:0; z-index:999; cursor: crosshair;"></div>
            </div>
       </div>

       <template #footer>
          <div class="dialog-footer">
            <el-button @click="printConfigVisible = false">取消</el-button>
            <el-button type="primary" @click="executePrint">应用排版并系统打印 (批量)</el-button>
          </div>
       </template>
    </el-dialog>

    <!-- 日志追溯弹层 -->
    <el-dialog v-model="logVisible" :title="`资产追溯审计: ${currentAsset?.asset_code || ''}`" width="600px">
       <div v-loading="logLoading" class="min-h-[200px] px-4">
         <el-timeline v-if="logs.length > 0" class="mt-4">
            <el-timeline-item
              v-for="log in logs"
              :key="log.id"
              :timestamp="new Date(log.created_at).toLocaleString()"
              :type="log.action.includes('新建') ? 'success' : 'primary'"
            >
              <div class="text-sm">
                <span class="font-medium text-gray-800">{{ log.action }}</span>
                <span class="text-xs text-gray-500 ml-2"><el-icon><User /></el-icon> {{ log.operator_name }}</span>
                <div v-if="log.previous_owner_name || log.new_owner_name" class="text-xs mt-1 text-blue-600 font-medium flex items-center space-x-1">
                   <span>[{{ log.previous_owner_name || '无归属' }}]</span>
                   <el-icon><Right /></el-icon>
                   <span>[{{ log.new_owner_name || '无归属' }}]</span>
                </div>
                <div class="text-xs mt-2 text-gray-500 bg-gray-50 p-2 rounded border">{{ log.memo }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无追溯记录" />
       </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { Plus, Refresh, Download, User, Right, Printer } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'
import QrcodeVue from 'qrcode.vue'

const loading = ref(false)
const uploading = ref(false)
const uploadHeaders = computed(() => {
    const token = localStorage.getItem('itom_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
})
const rawAssets = ref<any[]>([])
const categories = ref<any[]>([])
const employees = ref<any[]>([])
const empLoading = ref(false)

const searchKeyword = ref('')
const searchStatus = ref('')
const searchCategory = ref<number | ''>('')

const fetchGlobals = async () => {
    try {
        const [catRes, empRes] = await Promise.all([
            axios.get('/api/assets/categories'),
            axios.get('/api/assets/employees', { params: { keyword: '' }}) 
        ])
        categories.value = catRes.data || []
        employees.value = empRes.data || []
    } catch {
        ElMessage.warning('拉取分类与人员基础数据失败')
    }
}

const fetchAssets = async () => {
    loading.value = true
    try {
        const { data } = await axios.get('/api/assets/')
        rawAssets.value = data || []
    } catch {
        ElMessage.error('无法拉取资产池数据')
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchGlobals()
    fetchAssets()
})

const filteredAssets = computed(() => {
    return rawAssets.value.filter(a => {
        let matchKw = true
        let matchSt = true
        let matchCat = true
        
        if (searchKeyword.value) {
            const kw = searchKeyword.value.toLowerCase()
            const code = (a.asset_code || '').toLowerCase()
            const ownerName = a.owner ? a.owner.name.toLowerCase() : ''
            matchKw = code.includes(kw) || ownerName.includes(kw)
        }
        if (searchStatus.value) {
            matchSt = a.status === searchStatus.value
        }
        if (searchCategory.value !== '') {
            matchCat = a.category_id === searchCategory.value
        }
        return matchKw && matchSt && matchCat
    })
})

const dynamicHeaders = computed(() => {
    const keys = new Set<string>()
    const excludedKeys = ['规格型号', '计量单位', '所属组织', '序列号', '备注'] // These are already statically rendered
    filteredAssets.value.forEach(asset => {
        if(asset.dynamic_attributes) {
            Object.keys(asset.dynamic_attributes).forEach(k => {
                if (!excludedKeys.includes(k)) {
                    keys.add(k)
                }
            })
        }
    })
    return Array.from(keys)
})

const getCategoryName = (id: number) => {
    const c = categories.value.find(x => x.id === id)
    return c ? c.name : '未知分类'
}

const getStatusType = (status: string) => {
    if(status === '在库') return 'success'
    if(status === '借用中') return 'primary'
    if(status === '维修中') return 'warning'
    return 'danger' // 报废
}

// ------ 抽屉功能 ------
const drawerVisible = ref(false)
const isNew = ref(true)
const submitLoading = ref(false)
const currentAsset = ref<any>(null)
const logs = ref<any[]>([])

// 为了演示，这里的人员搜索暂时在刚才拉的假数据里找，如果需要从AD实时搜索可以通过改造下面这块。
const searchEmployees = async (query: string) => {
    if (!query) return;
    empLoading.value = true
    try {
       const { data } = await axios.get('/api/assets/employees', { params: { keyword: query } }) 
       employees.value = data || []
    } finally {
       empLoading.value = false
    }
}

const form = ref<any>({
    asset_code: '',
    category_id: undefined,
    status: '在库',
    owner_id: undefined,
    dynamic_attributes: {}
})

const currentCatTpl = computed(() => {
    if(!form.value.category_id) return {}
    const c = categories.value.find(x => x.id === form.value.category_id)
    return c?.default_attributes || {}
})

const handleCategoryChange = (_val: number) => {
    if(isNew.value) {
        // 重置动态表单并填入 key
        const tpl = currentCatTpl.value
        const dict: any = {}
        Object.keys(tpl).forEach(k => dict[k] = '')
        form.value.dynamic_attributes = dict
    }
}

const handleStatusChange = (val: string) => {
    if(val === '在库' || val === '已归档/报废') {
        form.value.owner_id = undefined
    }
}

const openCreateDrawer = () => {
    isNew.value = true
    currentAsset.value = null
    logs.value = []
    form.value = {
        asset_code: '',
        category_id: undefined,
        status: '在库',
        owner_id: undefined,
        created_at: undefined,
        dynamic_attributes: {}
    }
    drawerVisible.value = true
}

const openManageDrawer = async (row: any) => {
    isNew.value = false
    currentAsset.value = row
    form.value = {
        asset_code: row.asset_code,
        category_id: row.category_id,
        status: row.status,
        owner_id: row.owner_id,
        created_at: row.created_at,
        dynamic_attributes: { ...row.dynamic_attributes }
    }
    
    // 补齐缺失的字段模板
    const tplKeys = Object.keys(currentCatTpl.value)
    tplKeys.forEach(k => {
        if(form.value.dynamic_attributes[k] === undefined) {
            form.value.dynamic_attributes[k] = ''
        }
    })
    
    drawerVisible.value = true
}

const logVisible = ref(false)
const logLoading = ref(false)
const openLogs = async (row: any) => {
    currentAsset.value = row
    logVisible.value = true
    logLoading.value = true
    try {
        const { data } = await axios.get(`/api/assets/${row.id}/logs`)
        logs.value = data || []
    } catch {
        ElMessage.warning('拉取审计流水失败')
    } finally {
        logLoading.value = false
    }
}

const submitSave = async () => {
    if(!form.value.asset_code || !form.value.category_id) {
        return ElMessage.warning('编号与分类为必填项')
    }
    submitLoading.value = true
    try {
        if(isNew.value) {
            await axios.post('/api/assets/', form.value)
            ElMessage.success('初次登记入库成功')
        } else {
            await axios.put(`/api/assets/${currentAsset.value.id}`, form.value)
            ElMessage.success('配置流转与修改成功')
        }
        drawerVisible.value = false
        fetchAssets()
    } catch(err:any) {
        ElMessage.error(err.response?.data?.detail || '保存失败')
    } finally {
        submitLoading.value = false
    }
}

const doArchive = async () => {
    try {
        await ElMessageBox.confirm('确定要将该资产强制作废并强制出库吗？该操作将被详细审计记录且通常不可逆！', '作废警报', { type: 'error'})
    } catch { return }
    
    submitLoading.value = true
    try {
        await axios.delete(`/api/assets/${currentAsset.value.id}`)
        ElMessage.success('成功置为报废状态并审计')
        drawerVisible.value = false
        fetchAssets()
    } catch(err:any) {
        ElMessage.error(err.response?.data?.detail || '作废执行失败')
    } finally {
        submitLoading.value = false
    }
}

const doHardDelete = async () => {
    try {
        await ElMessageBox.confirm('您正在执行彻底删除操作！该资产及其产生的所有审计日志都将被从数据库中永久移除，无法恢复，确定要继续吗？', '彻底删除警告', { 
            type: 'error',
            confirmButtonText: '极其确定',
            confirmButtonClass: 'el-button--danger'
        })
    } catch { return }
    
    submitLoading.value = true
    try {
        await axios.delete(`/api/assets/hard/${currentAsset.value.id}`)
        ElMessage.success('成功从数据库彻底移除资产')
        drawerVisible.value = false
        fetchAssets()
    } catch(err:any) {
        ElMessage.error(err.response?.data?.detail || '彻底删除执行失败')
    } finally {
        submitLoading.value = false
    }
}

const exportExcel = () => {
    if (filteredAssets.value.length === 0) return ElMessage.warning('当前暂无数据可导出')
    
    const rows = filteredAssets.value.map(a => {
        const baseRow: any = {
            '资产状态': a.status,
            '资产编码': a.asset_code,
            '资产分类': getCategoryName(a.category_id),
            '规格型号': a.dynamic_attributes ? (a.dynamic_attributes['规格型号'] || '') : '',
            '计量单位': a.dynamic_attributes && a.dynamic_attributes['计量单位'] ? a.dynamic_attributes['计量单位'] : '台/件',
            '入库日期': new Date(a.created_at).toLocaleDateString(),
            '所属组织': a.owner ? a.owner.department : (a.dynamic_attributes ? (a.dynamic_attributes['所属组织'] || '') : ''),
            '使用人': a.owner ? a.owner.name : '',
            '序列号': a.dynamic_attributes ? (a.dynamic_attributes['序列号'] || '') : '',
            '备注': a.dynamic_attributes ? (a.dynamic_attributes['备注'] || '') : ''
        }
        
        // Append any other dynamic headers that are not part of the core 10
        dynamicHeaders.value.forEach(h => {
             baseRow[h] = a.dynamic_attributes ? (a.dynamic_attributes[h] || '') : ''
        })
        
        return baseRow
    })

    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "资产台账导出")
    XLSX.writeFile(wb, `IT资产台账导出_${new Date().getTime()}.xlsx`)
}

// ------ 批量打印核心逻辑 ------
const selectedAssets = ref<any[]>([])
const handleSelectionChange = (val: any[]) => {
    selectedAssets.value = val
}

const assetsToPrint = ref<any[]>([])

const printConfigVisible = ref(false)
const printConfig = ref({
    width: 70,       // mm
    height: 50,      // mm
    padding: 2,      // mm
    border: 2,       // px
    rows: {
        r1: 12,
        r2: 8,
        r3: 8,
        r4: 8,
        r5: 6,
        r6: 6
    },
    fonts: {
        title: 15,
        code: 13,
        name: 13,
        spec: 13,
        serial: 13,
        date: 13
    },
    leftColWidth: 62,// % (文本占比宽度，剩余为二维码宽度)
    qrSize: 62       // px
})

// ----- 拖拽互动状态 -----
type FontKey = 'title' | 'code' | 'name' | 'spec' | 'serial' | 'date'
const selectedElement = ref<FontKey | 'qr' | string | null>(null)
const isDragging = ref(false)
const dragType = ref<string | null>(null)
const startY = ref(0)

const startValue = ref(0) // 记录按下时的原始高度或宽度百分比

const selectElement = (el: FontKey | 'qr' | string | null) => {
    selectedElement.value = el
}

const setHandleBg = (e: MouseEvent, active: boolean) => {
    const target = e.target as HTMLElement | null
    if (target) {
        target.style.background = active ? 'rgba(0,120,250,0.5)' : 'rgba(0,120,250,0)'
    }
}

const startDragRow = (e: MouseEvent, rowKey: string) => {
    isDragging.value = true
    dragType.value = 'row_' + rowKey
    startY.value = e.clientY
    // 强制断言，因为行高是已知 key
    startValue.value = (printConfig.value.rows as Record<string, number>)[rowKey] || 0
}


const onDrag = (e: MouseEvent) => {
    if (!isDragging.value) return
    e.preventDefault()
    
    // 简单粗糙的换算系统，1物理像素约等于0.2毫米 或在屏幕上按实际伸缩计算，这里我们用估算比例：通常屏幕1mm = 3.8px左右
    // 我们为了手感流畅，拖动10像素 = 1mm 
    if (dragType.value?.startsWith('row_')) {
        const rowKey = dragType.value.split('_')[1]!
        const deltaPx = e.clientY - startY.value
        const deltaMm = deltaPx / 4  // 灵敏度换算
        const newVal = Math.max(3, startValue.value + deltaMm) // 最少3毫米
        ;(printConfig.value.rows as Record<string, number>)[rowKey] = Number(newVal.toFixed(1))
    }
}

const stopDrag = () => {
    if (isDragging.value) {
        isDragging.value = false
        dragType.value = null
    }
}

const getQrUrl = (asset: any) => {
    return asset.qr_code_token ? `${window.location.origin}/mobile/asset/${asset.qr_code_token}` : window.location.origin
}

const printBatchLabels = (overrideAssets?: any[]) => {
    const targets = overrideAssets || selectedAssets.value
    if (targets.length === 0) return ElMessage.warning('请先选择要打印的资产项')
    
    // 赋值引发 Vue 重新渲染隐藏区的 DOM 与 QRCode
    assetsToPrint.value = targets
    printConfigVisible.value = true
}

const executePrint = async () => {
    printConfigVisible.value = false
    const loadingInstance = ElMessage({
        message: '正在生成高精度打印排版...',
        type: 'info',
        duration: 0
    })

    // 等待 DOM 更新和组件渲染完成
    await nextTick()
    setTimeout(() => {
        loadingInstance.close()
        const printArea = document.getElementById('batch-print-area')
        if (!printArea) return
        
        const printWindow = window.open('', '_blank')
        if (!printWindow) return ElMessage.error('无法弹出打印窗口，请检查浏览器拦截设置')
        
        printWindow.document.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <title>批量定制排版打印标签</title>
              <style>
                 body { margin: 0; padding: 0; background: #ccc; display: flex; flex-direction: column; align-items: center; }
                 @media print {
                     @page { margin: 0; size: ${printConfig.value.width}mm ${printConfig.value.height}mm; }
                     body { background: white; align-items: flex-start; }
                     .print-label-page { box-shadow: none !important; margin: 0 !important; }
                 }
                 .print-label-page { box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px 0; }
              </style>
            </head>
            <body>
              ${printArea.innerHTML}
            </body>
          </html>
        `)
        printWindow.document.close()
        
        setTimeout(() => {
            printWindow.focus()
            printWindow.print()
        }, 500)
    }, 400) // 延迟确保 SVG 渲染就绪
}

// ------ 导入功能 ------
const downloadTemplate = () => {
    const headers = ['资产状态', '资产编码', '资产分类', '规格型号', '计量单位', '入库日期', '所属组织', '使用人', '序列号', '备注']
    const exampleRow = ['在库', 'IT-PC-2023001', '笔记本', 'ThinkPad T14', '台', '2023-10-01', '研发中心', '张三', 'PF123456', '全新设备']
    const ws = XLSX.utils.aoa_to_sheet([headers, exampleRow])
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '导入模板')
    XLSX.writeFile(wb, '资产导入模板.xlsx')
}

const beforeUpload = (file: any) => {
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
    if (!isExcel) {
        ElMessage.error('上传文件只能是 xlsx 或 xls 格式!')
        return false
    }
    uploading.value = true
    return true
}

const handleUploadSuccess = (response: any) => {
    uploading.value = false
    if (response && response.success !== undefined) {
        ElMessage.success(`导入完成，成功 ${response.success} 条，失败 ${response.errors?.length || 0} 条`)
        if (response.errors && response.errors.length > 0) {
            console.warn("导入错误:", response.errors)
            ElMessageBox.alert(
                `<div style="max-height: 200px; overflow-y: auto;">
                  ${response.errors.map((e:string) => `<div>${e}</div>`).join('')}
                 </div>`,
                '部分导入失败详情',
                { dangerouslyUseHTMLString: true }
            )
        }
    } else {
        ElMessage.success('导入成功')
    }
    fetchAssets()
}

const handleUploadError = (err: any) => {
    uploading.value = false
    try {
        const errorData = JSON.parse(err.message)
        ElMessage.error(`导入失败: ${errorData.detail || '未知原因'}`)
    } catch {
        ElMessage.error('网络或服务器未响应，导入失败')
    }
}
</script>
