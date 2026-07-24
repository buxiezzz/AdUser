<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";

// --- 分钟无交互自动登出保护 ---
const INACTIVITY_TIMEOUT = 30 * 60 * 1000 
let t: any = null

const resetTimer = () => {
  if (t) clearTimeout(t)
  t = setTimeout(() => {
    if (uni.getStorageSync('itom_token')) {
      uni.removeStorageSync('itom_token')
      uni.reLaunch({ url: '/pages/login/login' })
      uni.showToast({ title: '会话已超时请重新登录', icon: 'none' })
    }
  }, INACTIVITY_TIMEOUT)
}

onLaunch(() => {
  console.log("App Launch")
  // 修复：移除强制清空服务器地址的代码，保证用户在手机端配置的 IP 能够永久生效
  resetTimer()
})
onShow(() => {
  console.log("App Show")
  resetTimer()
})
onHide(() => {
  console.log("App Hide")
})
</script>
<style></style>
