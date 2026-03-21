export const config = {
  // 默认使用测试环境 API
  // 注意：在真机调试/运行 App 时，不能使用 localhost 或 127.0.0.1
  // 请将此处替换为您的电脑的实际局域网 IP (例如: http://192.168.1.100:18000/api) 
  // 或者是实际的线上服务器域名
  baseUrl: import.meta.env.VITE_APP_BASE_URL || 'http://192.168.110.69:18000/api',
  timeout: 15000,
}
