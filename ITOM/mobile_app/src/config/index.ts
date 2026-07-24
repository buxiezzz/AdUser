// 默认的备用地址（开发时用，真机App以用户设置的地址为准）
const DEFAULT_BASE_URL = 'http://127.0.0.1:18000/api'

/**
 * 获取当前生效的服务器地址：
 * 优先读取用户在登录页手动设置的地址（存储在本地），没有则使用默认值
 */
export function getBaseUrl(): string {
  // #ifdef H5
  // 在 H5 浏览器调试时，无条件使用同源反向代理，彻底杜绝所有跨域与浏览器 PNA 限制，直接忽略任何本地残留缓存
  return '/api'
  // #endif

  const savedUrl = uni.getStorageSync('itom_server_url')
  if (savedUrl) return savedUrl

  return import.meta.env.VITE_APP_BASE_URL || DEFAULT_BASE_URL
}

export const config = {
  // baseUrl 改为动态读取，不再硬编码 IP
  get baseUrl() {
    return getBaseUrl()
  },
  timeout: 15000,
}
