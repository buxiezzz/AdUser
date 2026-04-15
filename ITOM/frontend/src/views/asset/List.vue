<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 tracking-tight">IT 资产台账与全生命周期管控</h1>
      <el-button type="primary" :icon="Plus" @click="openCreateDrawer">资产录入登记</el-button>
    </div>

    <!-- 顶层汇总状态卡片 / 过滤器 -->
    <el-card shadow="never" class="border-0 ring-1 ring-gray-100 rounded-xl">
      <!-- 第一行：搜索栏 + 操作按鈕 -->
      <div class="flex flex-wrap gap-3 mb-3">
        <el-input v-model="searchKeyword" placeholder="检索资产编号、初始关键词..." prefix-icon="Search" class="w-72" clearable />
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
      </div>

      <!-- 第二行：多维度筛选条 -->
      <div class="flex flex-wrap gap-3 items-center pb-4 border-b border-gray-100 mb-4">
        <el-select v-model="searchStatus" placeholder="资产状态" clearable class="w-32">
          <el-option label="闲置" value="闲置" />
          <el-option label="在用" value="在用" />
          <el-option label="维修" value="维修" />
          <el-option label="报废" value="报废" />
          <el-option label="下账" value="下账" />
        </el-select>

        <el-select v-model="searchLocation" placeholder="归属地" clearable class="w-36" v-if="isGroupAdmin">
          <el-option label="全部归属地" :value="0" />
          <el-option v-for="loc in locationList" :key="loc.id" :label="loc.name" :value="loc.id" />
        </el-select>

        <el-select v-model="searchCategory" placeholder="设备类型" clearable class="w-36">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>

        <el-input v-model="searchOwner" placeholder="使用人姓名" clearable class="w-36" />

        <el-select v-model="searchDept" placeholder="所属组织" clearable class="w-44" filterable>
          <el-option v-for="d in uniqueDepts" :key="d" :label="d" :value="d" />
        </el-select>

        <el-date-picker
          v-model="searchDateRange"
          type="daterange"
          start-placeholder="入库开始日"
          end-placeholder="入库结束日"
          value-format="YYYY-MM-DD"
          class="w-64"
          clearable
        />

        <el-button
          v-if="searchStatus || searchCategory || searchOwner || searchDept || searchDateRange || searchLocation"
          type="warning" plain size="small"
          @click="resetFilters"
        >重置全部筛选</el-button>

        <span class="text-xs text-gray-400 ml-auto">{{ totalAssets }} 条匹配资产</span>
      </div>

      <!-- 批量操作浮动栏（勾选>0时展示） -->
      <transition name="el-fade-in-linear">
        <div v-if="selectedAssets.length > 0" class="flex items-center gap-3 px-4 py-3 mb-3 bg-blue-50 rounded-xl border border-blue-200">
          <el-icon class="text-blue-600"><Select /></el-icon>
          <span class="text-sm text-blue-700 font-semibold">已选 {{ selectedAssets.length }} 项资产</span>
          <el-divider direction="vertical" />
          <el-button size="small" type="primary" plain @click="printBatchLabels()">批量打印</el-button>
          <el-button size="small" type="danger" plain @click="doBatchDelete">批量删除</el-button>
          <el-button size="small" plain @click="doClearSelection">取消选择</el-button>
        </div>
      </transition>

      <el-table ref="tableRef" :data="rawAssets" style="width: 100%" v-loading="loading" border stripe @selection-change="handleSelectionChange" @sort-change="handleSortChange" @row-click="handleRowClick" row-class-name="cursor-pointer">
         <el-table-column type="selection" width="55" fixed="left" />
         <el-table-column prop="status" label="资产状态" width="110" sortable="custom">
           <template #default="{ row }">
             <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column prop="asset_code" label="资产编码" width="180" sortable="custom">
            <template #default="{ row }">
              <span class="font-mono font-medium text-indigo-600">
                {{ row.asset_code || '未分配编号' }}
              </span>
            </template>
         </el-table-column>
         <el-table-column prop="category_name" label="资产名称" width="120" sortable="custom">
           <template #default="{ row }">
             <el-tag size="small" type="info">{{ getCategoryName(row.category_id) }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column prop="location_name" label="归属地" width="120" v-if="isGroupAdmin">
           <template #default="{ row }">
             <el-tag v-if="row.location" size="small" effect="plain" type="warning">{{ row.location.name }}</el-tag>
             <span v-else class="text-gray-400 text-sm">未分配</span>
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
         <el-table-column prop="created_at" label="入库日期" width="160" sortable="custom">
            <template #default="{ row }">
              <span class="text-gray-600 text-sm">{{ new Date(row.created_at).toLocaleDateString() }}</span>
            </template>
         </el-table-column>
         <el-table-column prop="department" label="所属组织" min-width="120" show-overflow-tooltip sortable="custom">
            <template #default="{ row }">
              <span class="text-gray-600">{{ row.owner ? row.owner.department : (row.dynamic_attributes ? row.dynamic_attributes['所属组织'] : '-') }}</span>
            </template>
         </el-table-column>
         <el-table-column prop="owner_name" label="使用人" width="150" show-overflow-tooltip sortable="custom">
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
      </el-table>

      <!-- 分页控制条 -->
      <div class="flex items-center justify-between mt-4 px-1">
        <span class="text-sm text-gray-500">共查询到 <b>{{ totalAssets }}</b> 条资产，当前第 {{ currentPage }} 页</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          layout="sizes, prev, pager, next, jumper"
          :total="totalAssets"
          background
          @current-change="handlePageChange"
          @size-change="handlePageChange"
        />
      </div>
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
                <el-option label="闲置" value="闲置" />
                <el-option label="在用" value="在用" />
                <el-option label="维修" value="维修" />
                <el-option label="报废" value="报废" />
                <el-option label="下账" value="下账" />
              </el-select>
            </el-form-item>
            <el-form-item label="资产编码" required>
              <el-input v-model="form.asset_code" placeholder="如 IT-PC-2023001" />
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2" v-if="isGroupAdmin">
            <el-form-item label="归属地">
              <el-select v-model="form.location_id" placeholder="选择归属地" clearable>
                <el-option v-for="loc in locationList" :key="loc.id" :label="loc.name" :value="loc.id" />
              </el-select>
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="资产分类" required>
              <el-select v-model="form.category_id" placeholder="选择资产类型" @change="handleCategoryChange">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
             <el-form-item label="规格型号">
               <el-autocomplete
                 v-model="form.dynamic_attributes['规格型号']"
                 :fetch-suggestions="querySpecs"
                 placeholder="如: ThinkPad T14"
                 clearable
                 class="w-full"
               />
             </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="计量单位">
               <el-autocomplete
                 v-model="form.dynamic_attributes['计量单位']"
                 :fetch-suggestions="queryUnits"
                 placeholder="台/件/套"
                 clearable
                 class="w-full"
               />
            </el-form-item>
            <el-form-item label="入库日期">
               <el-date-picker v-if="!isNew" v-model="form.created_at" type="datetime" disabled class="w-full" />
               <el-input v-else placeholder="保存后系统自动生成" disabled />
            </el-form-item>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-2">
            <el-form-item label="所属组织">
               <el-input
                 v-model="form.dynamic_attributes['所属组织']"
                 :placeholder="form.owner_id ? '' : '选择使用人后自动带入'"
                 :disabled="!!form.owner_id"
               />
               <div v-if="form.owner_id" class="text-xs text-blue-400 mt-1">归属组织由使用人信息自动带入，不可手动修改。</div>
            </el-form-item>
            <el-form-item label="使用人" class="flex-1">
              <el-select
                v-model="form.owner_id"
                filterable
                remote
                clearable
                placeholder="键入检索 AD 域用户"
                :remote-method="searchEmployees"
                :loading="empLoading"
                :disabled="form.status === '闲置' || form.status === '报废' || form.status === '下账'"
                @change="handleOwnerChange"
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
              <div v-if="form.status === '闲置' || form.status === '报废' || form.status === '下账'" class="text-xs text-gray-400 mt-1">闲置、报废或下账状态下不可绑定人。</div>
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

          <div class="mt-8 flex flex-wrap gap-4 justify-between items-center border-t border-gray-100 pt-5">
            <div class="flex gap-2">
                <el-button type="info" plain size="small" v-if="!isNew" @click="openLogs(currentAsset)">追溯流转日志</el-button>
                <el-button type="success" plain size="small" v-if="!isNew" @click="printBatchLabels([currentAsset])">打印资产标签</el-button>
                <el-button type="warning" plain size="small" v-if="!isNew" @click="doCopyAsset(currentAsset)">借此复制新建</el-button>
            </div>
            <div class="flex gap-2 items-center">
                <el-button @click="drawerVisible = false">取消</el-button>
                <el-button type="danger" plain v-if="!isNew && form.status !== '报废' && form.status !== '下账'" @click="doArchive">报废与归档</el-button>
                <el-button type="danger" v-if="!isNew" @click="doHardDelete">彻底删除台账</el-button>
                <el-button type="primary" @click="submitSave">保存提交档案</el-button>
            </div>
          </div>
        </el-form>
      </div>
    </el-drawer>

    <!-- 隐藏的渲染区域，用于生成含有二维码的DOM给打印机 -->
    <div id="batch-print-area" style="position: absolute; left: -9999px; top: -9999px; width: 70mm; opacity: 0; pointer-events: none;">
      <div v-for="asset in assetsToPrint" :key="asset.id" class="print-label-page" :style="{ width: printConfig.width + 'mm', height: printConfig.height + 'mm', boxSizing: 'border-box', padding: printConfig.padding + 'mm', pageBreakAfter: 'always', display: 'flex', flexDirection: 'column', background: 'white', color: 'black', fontFamily: '\'Helvetica Neue\', Helvetica, Arial, sans-serif', overflow: 'hidden' }">
        <table :style="{ width: '100%', height: '100%', borderCollapse: 'collapse', border: printConfig.border + 'px solid black', fontWeight: 'bold', tableLayout: 'fixed' }">
          <colgroup>
            <col :style="{ width: (100 - (printConfig.qrColWidth || 30)) + '%' }" />
            <col :style="{ width: (printConfig.qrColWidth || 30) + '%' }" />
          </colgroup>
          <tbody>
          <tr>
            <td colspan="2" :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r1 + 'mm', padding: 0, textAlign: 'center', fontSize: printConfig.fonts.title + 'px', fontWeight: 900, letterSpacing: '-0.5px', whiteSpace: 'nowrap', overflow: 'hidden' }">{{ printConfig.company_name }}</td>
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
                <qrcode-vue :value="getQrUrl(asset)" :size="printConfig.qrSize" level="L" render-as="svg" style="display:block; margin: 0 auto;" />
             </td>
          </tr>
          <tr>
             <td :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r6 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.date + 'px', borderRight: 'none', whiteSpace: 'nowrap', overflow: 'hidden' }">使用日期: {{ new Date(asset.created_at).toISOString().split('T')[0] }}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- WYSIWYG 可视化打印排版设计器 -->
    <el-dialog v-model="printConfigVisible" title="定制修改打印排版与实时预览" width="900px" align-center @close="stopDrag">
       <!-- 顶部全局工具栏 -->
       <div class="flex flex-wrap items-center gap-4 bg-gray-50 p-3 rounded mb-4 border border-gray-200">
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
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">组织/公司抬头</span>
           <el-input v-model="printConfig.company_name" size="small" style="width: 200px" placeholder="输入打印抬头" />
         </div>
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">二维码区占比(%)</span>
           <el-slider v-model="printConfig.qrColWidth" :min="15" :max="60" style="width: 100px; margin-left: 10px; margin-right: 15px;" />
         </div>
         <div class="flex items-center gap-2">
           <span class="text-sm text-gray-600">二维码大小(px)</span>
           <el-input-number v-model="printConfig.qrSize" :min="10" :max="150" size="small" style="width: 100px" />
         </div>
         
         <el-divider direction="vertical" />

         <!-- 动态选中元素字号调节 (类似Word) -->
         <div class="flex items-center gap-2" v-if="selectedElement && selectedElement !== 'qr'">
           <span class="text-sm font-bold text-blue-600">当前选中文字字号(px)</span>
           <el-input-number v-model="(printConfig.fonts as any)[selectedElement]" :min="8" :max="50" size="small" style="width: 100px" />
         </div>
         <div v-else class="text-sm text-gray-400 italic">单击表格内文字以调节该行字号大小...</div>
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
                  <col :style="{ width: (100 - (printConfig.qrColWidth || 30)) + '%' }" />
                  <col :style="{ width: (printConfig.qrColWidth || 30) + '%' }" />
                </colgroup>
                <tbody>
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
                    {{ printConfig.company_name }}
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
                      <qrcode-vue :value="getQrUrl(assetsToPrint[0])" :size="printConfig.qrSize" level="L" render-as="svg" style="display:block; margin: 0 auto; pointer-events: none;" />
                   </td>
                </tr>
                <!-- Row 6 -->
                <tr>
                   <td @mousedown.stop="selectElement('date')"
                       :style="{ border: printConfig.border + 'px solid black', height: printConfig.rows.r6 + 'mm', padding: '0 2mm', fontSize: printConfig.fonts.date + 'px', borderRight: 'none', whiteSpace: 'nowrap', overflow: 'hidden', position: 'relative', outline: selectedElement === 'date' ? '2px dashed blue' : 'none', outlineOffset: '-2px', cursor: 'pointer' }">
                      使用日期: {{ new Date(assetsToPrint[0].created_at).toISOString().split('T')[0] }}
                   </td>
                </tr>
                </tbody>
              </table>
              <div v-if="isDragging" style="position:fixed; top:0; left:0; right:0; bottom:0; z-index:999; cursor: crosshair;"></div>
            </div>
       </div>

       <template #footer>
          <div class="dialog-footer flex justify-between items-center">
            <div>
               <el-button type="warning" plain @click="saveTemplateToSystem" :loading="savingTemplate">保存为默认模板</el-button>
               <span class="text-xs text-gray-400 ml-2">保存后下次打印将默认使用此排版</span>
            </div>
            <div>
              <el-button @click="printConfigVisible = false">取消</el-button>
              <el-button type="primary" @click="executePrint">应用排版并系统打印 (批量)</el-button>
            </div>
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Plus, Refresh, Download, User, Right, Select } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
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
const searchOwner = ref('')
const searchDept = ref('')
const searchDateRange = ref<string[] | null>(null)
const searchLocation = ref<number | ''>(0)
const savingTemplate = ref(false)

// 归属地相关
const locationList = ref<any[]>([])
const isGroupAdmin = ref(false)
const userLocationId = ref<number | null>(null)

// 从当前数据中提炼唯一的部门列表供下拉选择
const uniqueDepts = computed(() => {
    const depts = new Set<string>()
    rawAssets.value.forEach(a => {
        const dept = a.owner ? a.owner.department : (a.dynamic_attributes?.['所属组织'] || '')
        if (dept) depts.add(dept)
    })
    return Array.from(depts).sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const resetFilters = () => {
    searchStatus.value = ''
    searchCategory.value = ''
    searchOwner.value = ''
    searchDept.value = ''
    searchDateRange.value = null
    searchLocation.value = 0
}

const fetchGlobals = async () => {
    try {
        const [catRes, empRes, settingsRes, locRes, userRes] = await Promise.all([
            axios.get('/api/assets/categories'),
            axios.get('/api/assets/employees', { params: { keyword: '' }}),
            axios.get('/api/settings/'),
            axios.get('/api/locations/'),
            axios.get('/api/auth/me')
        ])
        categories.value = catRes.data || []
        employees.value = empRes.data || []
        
        if (settingsRes.data && settingsRes.data.PRINT_TEMPLATE) {
            printConfig.value = { ...printConfig.value, ...settingsRes.data.PRINT_TEMPLATE }
        }

        // 归属地和用户信息
        locationList.value = locRes.data || []
        isGroupAdmin.value = userRes.data?.is_group_admin || false
        userLocationId.value = userRes.data?.location_id || null
    } catch {
        ElMessage.warning('拉取分类、人员或全局配置数据失败')
    }
}

// 移除了冲突的 fetchAssets 定义，统一使用下面的服务端逻辑

onMounted(() => {
    fetchGlobals()
    fetchAssets()
})

// 分页与排序状态
const currentPage = ref(1)
const pageSize = ref(20)
const totalAssets = ref(0)
const sortProp = ref('updated_at')
const sortOrder = ref('desc')

// 获取资产列表 (服务端驱动)
const fetchAssets = async () => {
    loading.value = true
    try {
        const params: any = {
            skip: (currentPage.value - 1) * pageSize.value,
            limit: pageSize.value,
            keyword: searchKeyword.value,
            status: searchStatus.value,
            sort_by: sortProp.value,
            order: sortOrder.value === 'ascending' ? 'asc' : 'desc'
        }
        
        // 归属地过滤：集团超管可手动切换，普通用户由后端自动过滤
        if (isGroupAdmin.value && searchLocation.value && searchLocation.value !== 0) {
            params.location_id = searchLocation.value
        }
        
        // 主数据请求：独立执行，绝对不能因 count 失败而被拖垮
        const dataRes = await axios.get('/api/assets/', { params })
        rawAssets.value = dataRes.data || []
        
        // 总数请求：独立执行，失败了只影响页码显示，不影响列表
        const countParams: any = { keyword: searchKeyword.value, status: searchStatus.value }
        if (isGroupAdmin.value && searchLocation.value && searchLocation.value !== 0) {
            countParams.location_id = searchLocation.value
        }
        axios.get('/api/assets/count', { 
            params: countParams
        }).then(countRes => {
            totalAssets.value = countRes.data || rawAssets.value.length
        }).catch(() => {
            // count 失败时用当前页数据量做降级估算
            totalAssets.value = rawAssets.value.length
        })
        
    } catch {
        ElMessage.error('无法拉取资产台账数据，请检查网络连接')
    } finally {
        loading.value = false
    }
}

// 监听筛选条件，增加防抖，避免频繁请求
let timer: any = null
watch([searchKeyword, searchStatus, searchCategory, searchOwner, searchDept, searchDateRange, searchLocation], () => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
        currentPage.value = 1
        fetchAssets()
    }, 300)
})

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
    sortProp.value = prop || 'updated_at'
    sortOrder.value = order || 'desc'
    fetchAssets()
}

const handlePageChange = () => {
    fetchAssets()
}

// 模拟动态属性列 (仅基于当前可视页)
const dynamicHeaders = computed(() => {
    const keys = new Set<string>()
    const excludedKeys = ['规格型号', '计量单位', '所属组织', '序列号', '备注']
    rawAssets.value.forEach(asset => {
        if(asset.dynamic_attributes) {
            Object.keys(asset.dynamic_attributes).forEach(k => {
                if (!excludedKeys.includes(k)) keys.add(k)
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
    if(status === '闲置') return 'success'
    if(status === '在用') return 'primary'
    if(status === '维修') return 'warning'
    if(status === '下账') return 'info'
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
       // 仅保留真实 AD 域用户，过滤掉批量导入时创建的本地迁移账户
       employees.value = (data || []).filter((e: any) => !e.ad_account?.startsWith('local_'))
    } finally {
       empLoading.value = false
    }
}

// 选中使用人时自动带入归属组织；清空时同步清空组织
const handleOwnerChange = (ownerId: number | undefined) => {
    if (!ownerId) {
        if (form.value.dynamic_attributes) {
            form.value.dynamic_attributes['所属组织'] = ''
        }
        return
    }
    const emp = employees.value.find((e: any) => e.id === ownerId)
    if (emp && form.value.dynamic_attributes) {
        form.value.dynamic_attributes['所属组织'] = emp.department || ''
    }
}

// ---- 联想输入：规格型号 ----
const querySpecs = (query: string, cb: (results: { value: string }[]) => void) => {
    const all = new Set<string>()
    rawAssets.value.forEach(a => {
        const v = a.dynamic_attributes?.['规格型号']
        if (v) all.add(String(v))
    })
    const items = Array.from(all)
        .filter(v => !query || v.toLowerCase().includes(query.toLowerCase()))
        .map(v => ({ value: v }))
    cb(items)
}

// ---- 联想输入：计量单位 ----
const UNIT_PRESETS = ['台', '件', '套', '个', '块', '条', '本', '张']
const queryUnits = (query: string, cb: (results: { value: string }[]) => void) => {
    const fromData = new Set<string>()
    rawAssets.value.forEach(a => {
        const v = a.dynamic_attributes?.['计量单位']
        if (v) fromData.add(String(v))
    })
    const all = Array.from(new Set([...UNIT_PRESETS, ...fromData]))
    cb(all.filter(v => !query || v.includes(query)).map(v => ({ value: v })))
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
    if(val === '闲置' || val === '报废' || val === '下账') {
        form.value.owner_id = null
        if (form.value.dynamic_attributes) {
            form.value.dynamic_attributes['所属组织'] = ''
        }
    }
}

const openCreateDrawer = () => {
    isNew.value = true
    currentAsset.value = null
    logs.value = []
    form.value = {
        asset_code: '',
        category_id: undefined,
        status: '闲置',
        owner_id: undefined,
        location_id: userLocationId.value || undefined,  // 自动带上归属地
        created_at: undefined,
        dynamic_attributes: { '计量单位': '台' }  // 默认单位为台
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
        location_id: row.location_id,
        created_at: row.created_at,
        dynamic_attributes: { ...row.dynamic_attributes }
    }
    
    // 关键修正：确保当前的使用人数据在 employees 下拉列表中，避免 el-select 因找不到 option 直接显示 id 数值
    if (row.owner) {
        if (!employees.value.find((e: any) => e.id === row.owner.id)) {
            employees.value.push(row.owner)
        }
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

const doCopyAsset = (row: any) => {
    isNew.value = true
    currentAsset.value = null
    logs.value = []
    
    // 生成复制品默认数据（状态为闲置，无使用人）
    form.value = {
        asset_code: `${row.asset_code}-COPY`, // 提示用户修改
        category_id: row.category_id,
        status: '闲置',
        owner_id: undefined,
        created_at: undefined,
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

const exportExcel = async () => {
    if (totalAssets.value === 0) return ElMessage.warning('当前暂无数据可导出')
    
    const exportLoading = ElLoading.service({
        lock: true,
        text: '全量导出涉及数据量较大，正在准备清单，请稍后...',
        background: 'rgba(0, 0, 0, 0.7)'
    })

    try {
        // 1. 获取全量数据 (不再受分页限制)
        const params: any = {
            skip: 0,
            limit: 100000, // 给一个足够大的数值模拟全量
            keyword: searchKeyword.value,
            status: searchStatus.value,
            sort_by: sortProp.value,
            order: sortOrder.value === 'ascending' ? 'asc' : 'desc'
        }
        
        const res = await axios.get('/api/assets/', { params })
        const allAssets = res.data || []
        
        if (allAssets.length === 0) {
            ElMessage.warning('未获取到数据')
            return
        }

        // 2. 转换数据逻辑
        const rows = allAssets.map(a => {
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
            
            dynamicHeaders.value.forEach(h => {
                 baseRow[h] = a.dynamic_attributes ? (a.dynamic_attributes[h] || '') : ''
            })
            
            return baseRow
        })

        const ws = XLSX.utils.json_to_sheet(rows)
        const wb = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(wb, ws, "资产台账导出")
        XLSX.writeFile(wb, `ITOM_资产台账_${new Date().getTime()}.xlsx`)
        ElMessage.success(`全量导出成功，共计 ${rows.length} 条记录`)
    } catch (err) {
        console.error(err)
        ElMessage.error('导出全量数据失败，请检查网络或咨询管理员')
    } finally {
        exportLoading.close()
    }
}

// ------ 批量打印核心逻辑 ------
const tableRef = ref<any>(null)
const selectedAssets = ref<any[]>([])
const handleSelectionChange = (val: any[]) => {
    selectedAssets.value = val
}

const handleRowClick = (row: any, column: any) => {
    if (!column) return;
    // 如果点击的是复选框列、或者点击了资产编码呼出气泡，都不触发抽屉弹出
    if (column.type === 'selection' || column.property === 'asset_code') {
        return;
    }
    openManageDrawer(row);
}

// ------ 批量操作 ------
const batchLoading = ref(false)

const doClearSelection = () => {
    tableRef.value?.clearSelection()
}

const doBatchDelete = async () => {
    try {
        await ElMessageBox.confirm(
            `确定要将选中的 ${selectedAssets.value.length} 台设备彻底删除吗？（不可恢复）`,
            '批量彻底删除确认', { type: 'warning' }
        )
    } catch { return }
    batchLoading.value = true
    try {
        const ids = selectedAssets.value.map((a: any) => a.id)
        const { data } = await axios.post('/api/assets/batch-delete', { asset_ids: ids })
        ElMessage.success(`成功彻底删除 ${data.deleted} 台设备`)
        doClearSelection()
        fetchAssets()
    } catch (err: any) {
        ElMessage.error(err.response?.data?.detail || '批量删除失败')
    } finally {
        batchLoading.value = false
    }
}

const assetsToPrint = ref<any[]>([])

const printConfigVisible = ref(false)
const printConfig = ref({
    width: 70,       // mm
    height: 50,      // mm
    padding: 2,      // mm
    border: 2,       // px
    margin_bottom: 0,
    company_name: '先惠自动化技术(武汉)有限责任公司', // default local value
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
    qrColWidth: 30,  // % (二维码整列占比，可以通过滑块调节实现中线左右平移)
    leftColWidth: 62,// % (原有预留备用属性)
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

const saveTemplateToSystem = async () => {
    savingTemplate.value = true
    try {
        await axios.post('/api/settings/', { print_template: printConfig.value })
        ElMessage.success('成功将当前排版保存为系统全局默认模板')
    } catch(err:any) {
        ElMessage.error(err.response?.data?.detail || '保存失败，可能需要管理员权限')
    } finally {
        savingTemplate.value = false
    }
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
