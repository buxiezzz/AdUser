// 默认的备用地址（开发时用，真机App以用户设置的地址为准）
const DEFAULT_BASE_URL = 'http://192.168.1.100:18000/api'

/**
 * 获取当前生效的服务器地址：
 * 优先读取用户在登录页手动设置的地址（存储在本地），没有则使用默认值
 */
export function getBaseUrl(): string {
  const savedUrl = uni.getStorageSync('itom_server_url')
  return savedUrl || import.meta.env.VITE_APP_BASE_URL || DEFAULT_BASE_URL
}

export const config = {
  // baseUrl 改为动态读取，不再硬编码 IP
  get baseUrl() {
    return getBaseUrl()
  },
  timeout: 15000,
}
