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
