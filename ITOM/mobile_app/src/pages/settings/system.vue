<template>
  <view class="container">

    <!-- 服务器地址设置区 -->
    <view class="server-card">
      <view class="server-title-row" @click="showServerSetting = !showServerSetting">
        <text class="server-title">🌐 后台服务器地址</text>
        <view style="display:flex;align-items:center;">
          <text class="server-ip">{{ displayServerUrl }}</text>
          <text class="arrow">{{ showServerSetting ? '▲' : '▼' }}</text>
        </view>
      </view>
      <view v-if="showServerSetting" class="server-form">
        <text class="hint">💡 换了网络后在此处更新电脑的局域网 IP</text>
        <view class="ip-row">
          <view class="input-group main">
            <text class="prefix">http://</text>
            <input class="ip-input" v-model="serverIp" placeholder="例如: 10.20.133.62" />
          </view>
          <view class="input-group port">
            <text class="sep">:</text>
            <input class="ip-input" v-model="serverPort" placeholder="18000" type="number" />
          </view>
          <text class="suffix">/api</text>
        </view>
        <button class="save-btn" size="mini" @click="saveServerUrl">保存并重试</button>
      </view>
    </view>

    <!-- ITOM 全局配置 -->
    <view class="card">
      <view class="section-title">ITOM 平台全局配置</view>
      <view class="desc">对 AD 域连接和基础设置进行配对。出于安全考量，密码类字段在移动端已遮蔽。</view>
      
      <view v-if="loading" class="loading-tip">加载中...</view>
      <view v-else-if="loadError" class="error-tip">⚠️ 无法连接到服务器，请检查上方服务器地址是否正确</view>
      <view v-else>
        <view class="config-item" v-for="(v, k) in configData" :key="k">
          <text class="label">{{ k }}</text>
          <view class="value-box">
            <text class="value" v-if="k.includes('PASSWORD')">********</text>
            <text class="value" v-else>{{ v }}</text>
          </view>
        </view>
      </view>
      
      <button class="edit-btn" @click="editConfig">修改全局配置</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { getBaseUrl } from '@/config'

const configData = ref<any>({})
const loading = ref(false)
const loadError = ref(false)
const showServerSetting = ref(false)
const serverIp = ref('')
const serverPort = ref('18000')

// 显示当前生效的 IP
const displayServerUrl = computed(() => {
  const url = getBaseUrl()
  const match = url.match(/http:\/\/([^/]+)/)
  return match ? match[1] : url
})

onMounted(() => {
  // 回显当前保存的 IP
  const saved = uni.getStorageSync('itom_server_url') as string
  if (saved) {
    // 匹配 http://ip:port/api 或 http://ip:port
    const match = saved.match(/http:\/\/([^:]+):(\d+)/)
    if (match) {
      serverIp.value = match[1]
      serverPort.value = match[2]
    }
  }
  loadConfig()
})

const saveServerUrl = () => {
  const ip = serverIp.value.trim()
  if (!ip) {
    uni.showToast({ title: '请输入 IP 地址', icon: 'none' })
    return
  }
  const ipReg = /^\d{1,3}(\.\d{1,3}){3}$/
  if (!ipReg.test(ip)) {
    uni.showToast({ title: 'IP 格式不正确', icon: 'none' })
    return
  }
  const port = serverPort.value.trim() || '18000'
  uni.setStorageSync('itom_server_url', `http://${ip}:${port}/api`)
  uni.showToast({ title: '地址已保存，正在重新连接...', icon: 'success' })
  showServerSetting.value = false
  // 重新加载配置
  setTimeout(() => loadConfig(), 500)
}

const loadConfig = async () => {
  loading.value = true
  loadError.value = false
  try {
    const res = await request.get('/settings/config')
    configData.value = res || {}
  } catch (e) {
    console.error(e)
    loadError.value = true
  } finally {
    loading.value = false
  }
}

const editConfig = () => {
  uni.showToast({ title: '核心系统配置请移步至 PC 大屏浏览器操作', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f7f9fb;
  padding: 15px;
}

/* 服务器地址卡片 */
.server-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);

  .server-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .server-title {
    font-size: 14px;
    color: #555;
    font-weight: 500;
  }
  .server-ip {
    font-size: 13px;
    color: #007aff;
    margin-right: 6px;
  }
  .arrow {
    font-size: 11px;
    color: #bbb;
  }
  .server-form {
    margin-top: 12px;
    background: #f7f9fb;
    border-radius: 8px;
    padding: 12px;
    .hint {
      font-size: 12px;
      color: #f59e0b;
      display: block;
      margin-bottom: 8px;
    }
    .ip-row {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .input-group {
        display: flex;
        align-items: center;
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0 10px;
        height: 42px;
        transition: border-color 0.2s;
        
        &:focus-within {
          border-color: #007aff;
        }
        
        &.main { flex: 1; }
        &.port { width: 90px; }
      }

      .prefix, .suffix, .sep {
        font-size: 13px;
        color: #999;
        flex-shrink: 0;
      }
      .sep {
        font-weight: bold;
        color: #333;
        margin: 0 2px;
      }
      
      .ip-input {
        flex: 1;
        font-size: 14px;
        height: 42px;
        min-width: 0;
        color: #333;
      }
    }
    .save-btn {
      margin-top: 12px;
      background: linear-gradient(135deg, #007aff, #0056b3);
      color: #fff;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      height: 40px;
      line-height: 40px;
      box-shadow: 0 4px 10px rgba(0, 122, 255, 0.2);
      &::after { border: none; }
      &:active { opacity: 0.9; transform: translateY(1px); }
    }
  }
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  
  .section-title {
    font-size: 18px;
    font-weight: bold;
    color: #333;
    margin-bottom: 8px;
  }
  
  .desc {
    font-size: 13px;
    color: #888;
    margin-bottom: 24px;
    line-height: 1.5;
  }

  .loading-tip {
    text-align: center;
    color: #999;
    font-size: 14px;
    padding: 20px 0;
  }

  .error-tip {
    background: #fff2f0;
    border-radius: 8px;
    padding: 12px;
    font-size: 13px;
    color: #ff4d4f;
    margin-bottom: 16px;
  }
  
  .config-item {
    margin-bottom: 16px;
    border-bottom: 1px solid #f9f9f9;
    padding-bottom: 10px;
    
    .label {
      font-size: 14px;
      color: #666;
      margin-bottom: 6px;
      display: block;
    }
    
    .value-box {
      .value {
        font-size: 15px;
        color: #333;
        word-break: break-all;
      }
    }
  }
  
  .edit-btn {
    margin-top: 30px;
    background: #007aff;
    color: #fff;
    border-radius: 8px;
    font-size: 16px;
    
    &::after { border: none; }
    &:active { background: #0062cc; }
  }
}
</style>
