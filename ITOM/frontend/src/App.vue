<template>
  <el-config-provider :zIndex="3000">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'

const router = useRouter()
const lastActivityTime = ref(Date.now())
const IDLE_TIMEOUT = 30 * 60 * 1000 // 30 分钟 (单位：毫秒)
let checkInterval: any = null

// 重置最后活跃时间
const resetActivity = () => {
    lastActivityTime.value = Date.now()
}

// 事件监听配置
const activityEvents = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']

const checkIdle = () => {
    const token = localStorage.getItem('itom_token')
    if (!token) return // 未登录状态不检测
    
    // 如果是移动端路径，则不受无操作自动登出限制（方便现场作业）
    if (window.location.pathname.startsWith('/mobile')) {
        return
    }

    const now = Date.now()
    if (now - lastActivityTime.value > IDLE_TIMEOUT) {
        // 执行自动登出
        performAutoLogout()
    }
}

const performAutoLogout = () => {
    localStorage.removeItem('itom_token')
    
    ElNotification({
        title: '安全提示',
        message: '由于您长时间未进行操作，系统已自动结束会话并退出登录。',
        type: 'warning',
        duration: 0, // 不自动关闭，引导用户注意
        position: 'top-right'
    })
    
    router.push('/login')
    // 强制清理以防残留
    clearInterval(checkInterval)
}

onMounted(() => {
    // 监听所有活跃事件
    activityEvents.forEach(event => {
        window.addEventListener(event, resetActivity, { passive: true })
    })

    // 每 10 秒检查一次是否超时
    checkInterval = setInterval(checkIdle, 10000)
})

onUnmounted(() => {
    // 清理监听器与定时器
    activityEvents.forEach(event => {
        window.removeEventListener(event, resetActivity)
    })
    if (checkInterval) clearInterval(checkInterval)
})
</script>


