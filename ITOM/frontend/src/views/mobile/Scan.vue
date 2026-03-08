<template>
  <div class="fixed inset-0 bg-black flex flex-col pt-safe-top overflow-hidden">
    <div class="p-4 flex items-center justify-between text-white z-20">
      <el-button circle size="large" @click="handleBack" type="info" plain class="bg-black/50 border-0">
        <el-icon :size="20"><ArrowLeft /></el-icon>
      </el-button>
      <h2 class="text-lg font-medium">扫描标签</h2>
      <div class="w-10"></div>
    </div>
    
    <div class="flex-1 relative bg-black">
      <qrcode-stream 
        @detect="onDetect" 
        @error="onError"
        :track="paintOutline"
        v-if="!scannedResult">
        <div class="absolute inset-0 flex flex-col items-center justify-center p-6 text-center z-10">
          <div class="w-64 h-64 border-2 border-dashed border-white/50 rounded-2xl flex items-center justify-center mb-6 relative">
            <!-- 扫描动画线 -->
            <div class="absolute left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_8px_2px_rgba(59,130,246,0.8)] animate-scan"></div>
            <p class="text-white/70 text-sm">将二维码放入框内</p>
            <div class="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-white rounded-tl-lg"></div>
            <div class="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-white rounded-tr-lg"></div>
            <div class="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-white rounded-bl-lg"></div>
            <div class="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-white rounded-br-lg"></div>
          </div>
        </div>
      </qrcode-stream>
      
      <div v-if="scannedResult" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 p-6 z-20">
        <div class="bg-white/10 p-4 rounded-full mb-4">
          <el-icon :size="48" class="text-emerald-400"><CircleCheckFilled /></el-icon>
        </div>
        <h3 class="text-white text-xl font-medium mb-2">识别成功</h3>
        <p class="text-gray-400 mb-8">{{ scannedResult }}</p>
        <p class="text-gray-300 text-sm text-center">正在跳转至资产详情页，请稍候...</p>
      </div>
    </div>

    <div v-if="error" class="absolute bottom-10 left-4 right-4 bg-red-500/90 backdrop-blur text-white p-4 rounded-xl shadow-lg z-30 flex items-center">
        <el-icon class="mr-3"><Warning /></el-icon>
        <span class="flex-1 text-sm">{{ error }}</span>
        <el-button link text type="primary" class="text-white" @click="error = ''">关闭</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { QrcodeStream } from 'vue-qrcode-reader'
import { ArrowLeft, Warning, CircleCheckFilled } from '@element-plus/icons-vue'

const router = useRouter()
const scannedResult = ref('')
const error = ref('')

// 返回上一页
const handleBack = () => {
  router.back()
}

// 识别处理
const onDetect = (detectedCodes: any[]) => {
  if (detectedCodes.length > 0) {
    let rawValue = detectedCodes[0].rawValue
    console.log('Scanned QR:', rawValue)
    
    // 如果扫出来是旧版标签（比如纯资产编码 WH0001, 或者只是序列号）
    // 或者即使扫出了新标签带链接的，也提取最后的 token
    let token = rawValue
    if (rawValue.includes('/mobile/asset/')) {
        const parts = rawValue.split('/mobile/asset/')
        token = parts[parts.length - 1]
    } else if (rawValue.includes('http')) {
        // 其他类型的链接，如果不是系统内部的则报错
        error.value = '无法识别该外链二维码'
        return
    }

    scannedResult.value = token
    
    // 延迟跳转体验
    setTimeout(() => {
        router.push(`/mobile/asset/${token}`)
    }, 800)
  }
}

const onError = (err: any) => {
  if (err.name === 'NotAllowedError') {
    error.value = '需要相机权限，请允许浏览器使用摄像头'
  } else if (err.name === 'NotFoundError') {
    error.value = '未检测到可用摄像头设备'
  } else if (err.name === 'NotSupportedError') {
    error.value = '当前环境不支持访问摄像头 (需 HTTPS 或 localhost)'
  } else if (err.name === 'NotReadableError') {
    error.value = '摄像头被占用'
  } else if (err.name === 'OverconstrainedError') {
    error.value = '无法找到合适的摄像头'
  } else if (err.name === 'StreamApiNotSupportedError') {
    error.value = '您的浏览器不支持摄像头流'
  } else {
    error.value = '相机初始化失败: ' + err.message
  }
}

// 可选：高亮扫码区域
const paintOutline = (detectedCodes: any, ctx: CanvasRenderingContext2D) => {
  for (const detectedCode of detectedCodes) {
    const [firstPoint, ...otherPoints] = detectedCode.cornerPoints
    ctx.strokeStyle = '#3b82f6' // blue-500
    ctx.lineWidth = 4
    ctx.beginPath()
    ctx.moveTo(firstPoint.x, firstPoint.y)
    for (const { x, y } of otherPoints) {
      ctx.lineTo(x, y)
    }
    ctx.lineTo(firstPoint.x, firstPoint.y)
    ctx.closePath()
    ctx.stroke()
  }
}
</script>

<style scoped>
@keyframes scan-animation {
  0% { top: 10%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 90%; opacity: 0; }
}

.animate-scan {
  animation: scan-animation 2s linear infinite;
}
</style>
