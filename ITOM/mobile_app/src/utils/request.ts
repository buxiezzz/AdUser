import { config } from '../config'

interface RequestOptions extends UniApp.RequestOptions {
  customHeader?: any
}

export const request = <T = any>(options: RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    // 获取 token
    const token = uni.getStorageSync('itom_token')
    
    // 初始化 header
    const header = {
      ...options.header,
      ...options.customHeader
    }
    
    // 如果存在 token 则附带
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    // 发起真实的 uni.request
    uni.request({
      url: options.url.startsWith('http') ? options.url : config.baseUrl + options.url,
      method: options.method || 'GET',
      data: options.data,
      header,
      timeout: config.timeout,
      success: (res) => {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data as T)
        } else if (res.statusCode === 401) {
          // Token 过期或无效
          uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none'
          })
          uni.removeStorageSync('itom_token')
          uni.reLaunch({
            url: '/pages/login/login'
          })
          reject(res)
        } else {
          uni.showToast({
            title: (res.data as any)?.detail || '请求失败',
            icon: 'none'
          })
          reject(res)
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '网络异常，请检查网络设置或配置的服务器IP',
          icon: 'none',
          duration: 3000
        })
        reject(err)
      }
    })
  })
}

// 暴露出快捷方法
export default {
  get: <T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method'>) => {
    return request<T>({ url, method: 'GET', data, ...options })
  },
  post: <T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method'>) => {
    return request<T>({ url, method: 'POST', data, ...options })
  },
  put: <T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method'>) => {
    return request<T>({ url, method: 'PUT', data, ...options })
  },
  delete: <T = any>(url: string, data?: any, options?: Omit<RequestOptions, 'url' | 'method'>) => {
    return request<T>({ url, method: 'DELETE', data, ...options })
  }
}
