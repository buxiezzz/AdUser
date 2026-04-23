<template>
  <view class="login-container">
    <view class="logo-box">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="app-name">SK 先惠 | ITOM 运维助手</text>
    </view>
    
    <view class="form-box">
      <!-- 服务器地址设置 -->
      <view class="server-row" @click="showServerSetting = !showServerSetting">
        <text class="server-label">⚙️ 服务器地址</text>
        <text class="server-value">{{ displayServerUrl }}</text>
        <text class="server-arrow">{{ showServerSetting ? '▲' : '▼' }}</text>
      </view>
      <view v-if="showServerSetting" class="server-setting-box">
        <text class="hint-text">💡 请填写运行本系统的电脑在局域网内的 IP 地址（端口 18000）</text>
        <view class="server-input-row">
          <text class="prefix">http://</text>
          <input
            class="server-input"
            v-model="serverIp"
            placeholder="例如: 10.20.108.159"
            @input="onServerIpInput"
          />
          <text class="port-sep">:</text>
          <input
            class="port-input"
            v-model="serverPort"
            placeholder="18000"
            type="number"
          />
          <text class="suffix">/api</text>
        </view>
        <button class="save-btn" size="mini" @click="saveServerUrl">保存并生效</button>
      </view>

      <view class="divider"></view>

      <view class="input-group">
        <text class="label">用户名</text>
        <input class="input" v-model="form.username" placeholder="请输入管理员账号" />
      </view>
      
      <view class="input-group">
        <text class="label">密码</text>
        <input class="input" password v-model="form.password" placeholder="请输入密码" />
      </view>
      
      <button class="login-btn" :loading="loading" @click="handleLogin">登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { config, getBaseUrl } from '@/config'

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const showServerSetting = ref(false)

// 分开保存 IP 和 端口
const serverIp = ref('')
const serverPort = ref('18000')

// 展示当前生效的服务器地址
const displayServerUrl = computed(() => {
  const url = getBaseUrl()
  const match = url.match(/http:\/\/([^/]+)/)
  return match ? match[1] : url
})

onMounted(() => {
  const saved = uni.getStorageSync('itom_server_url') as string
  if (saved) {
    const match = saved.match(/http:\/\/([^:]+):(\d+)/)
    if (match) {
      serverIp.value = match[1]
      serverPort.value = match[2]
    }
  }
})

const onServerIpInput = () => {
  serverIp.value = serverIp.value.trim()
}

const saveServerUrl = () => {
  const ip = serverIp.value.trim()
  const port = serverPort.value.trim() || '18000'
  if (!ip) {
    uni.showToast({ title: '请输入 IP 地址', icon: 'none' })
    return
  }
  const fullUrl = `http://${ip}:${port}/api`
  uni.setStorageSync('itom_server_url', fullUrl)
  uni.showToast({ title: '配置已更新', icon: 'success' })
  showServerSetting.value = false
}

const handleLogin = async () => {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
    return
  }
  
  loading.value = true
  try {
    const res = await uni.request({
      url: config.baseUrl + '/auth/login',
      method: 'POST',
      header: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      data: {
        username: form.username,
        password: form.password
      }
    })
    
    const data = res.data as any
    if (data && data.access_token) {
      uni.setStorageSync('itom_token', data.access_token)
      uni.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 1000)
    } else {
      uni.showToast({ title: data.detail || '登录失败', icon: 'none' })
    }
  } catch (err) {
    console.error('Login failed', err)
    uni.showToast({ title: '连接失败，请检查服务器地址是否正确', icon: 'none', duration: 3000 })
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  padding: 40px 30px;
  min-height: 100vh;
  background-color: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.logo-box {
  margin-top: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60px;
  
  .logo {
    width: 80px;
    height: 80px;
    margin-bottom: 16px;
    background-color: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }
  
  .app-name {
    font-size: 24px;
    font-weight: bold;
    color: #333;
  }
}

.form-box {
  background: #fff;
  padding: 30px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  
  /* 服务器地址折叠行 */
  .server-row {
    display: flex;
    align-items: center;
    padding: 6px 0 12px;
    cursor: pointer;
    
    .server-label {
      font-size: 13px;
      color: #888;
      flex-shrink: 0;
    }
    .server-value {
      flex: 1;
      font-size: 12px;
      color: #e51923;
      margin: 0 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .server-arrow {
      font-size: 11px;
      color: #bbb;
    }
  }

  .server-setting-box {
    background: #f7f9fb;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 16px;

    .hint-text {
      font-size: 12px;
      color: #f59e0b;
      line-height: 1.6;
      display: block;
      margin-bottom: 10px;
    }

    .server-input-row {
      display: flex;
      align-items: center;
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 0 8px;
      height: 40px;

      .prefix, .suffix {
        font-size: 13px;
        color: #999;
        flex-shrink: 0;
      }

      .server-input {
        flex: 1;
        font-size: 14px;
        height: 40px;
        padding: 0 4px;
        min-width: 0;
      }

      .port-sep {
        font-size: 14px;
        color: #333;
        font-weight: bold;
        margin: 0 4px;
      }

      .port-input {
        width: 50px;
        font-size: 14px;
        height: 40px;
        color: #e51923;
        text-align: center;
      }
    }

    .save-btn {
      margin-top: 10px;
      background-color: #e51923;
      color: #fff;
      border-radius: 6px;
      font-size: 13px;
      
      &::after { border: none; }
    }
  }

  .divider {
    height: 1px;
    background: #f0f0f0;
    margin: 4px 0 20px;
  }

  .input-group {
    margin-bottom: 24px;
    
    .label {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
      display: block;
    }
    
    .input {
      height: 44px;
      border-bottom: 1px solid #eee;
      font-size: 16px;
      padding: 0 8px;
      transition: all 0.3s;
      
      &:focus {
        border-bottom-color: #e51923;
      }
    }
  }
  
  .login-btn {
    margin-top: 40px;
    background-color: #e51923;
    color: #fff;
    border-radius: 8px;
    font-size: 16px;
    
    &::after {
      border: none;
    }
    
    &:active {
      background-color: #b91c1c;
    }
  }
}
</style>
