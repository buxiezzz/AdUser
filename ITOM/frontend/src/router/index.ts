import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import axios from 'axios'

import MobileLayout from '../layouts/MobileLayout.vue'

// 1. 抽取通用的后台路由模块，双端可 100% 自动同步扩展
const adminRoutes: Array<any> = [
    {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '控制台概览' }
    },
    {
        path: 'assets/list',
        name: 'AssetList',
        component: () => import('../views/asset/List.vue'),
        meta: { title: '资产台账总览' }
    },
    {
        path: 'assets/categories',
        name: 'AssetCategories',
        component: () => import('../views/asset/Categories.vue'),
        meta: { title: '资产分类字典' }
    },
    {
        path: 'assets/transfers',
        name: 'AssetTransfers',
        component: () => import('../views/asset/TransferList.vue'),
        meta: { title: '跨归属地调拨申请' }
    },
    {
        path: 'assets/logs',
        name: 'AssetLogs',
        component: () => import('../views/audit/LogList.vue'),
        meta: { title: '资产操作日志', module: 'asset' }
    },
    {
        path: 'ad/provision',
        name: 'ADProvision',
        component: () => import('../views/ad/Provision.vue'),
        meta: { title: '一键创建域账号' }
    },
    {
        path: 'ad/filter',
        name: 'ADRegionFilter',
        component: () => import('../views/ad/RegionFilter.vue'),
        meta: { title: '地区过滤器' }
    },
    {
        path: 'ad/users',
        name: 'ADUsers',
        component: () => import('../views/ad/Users.vue'),
        meta: { title: '域用户检索' }
    },
    {
        path: 'ad/groups',
        name: 'ADGroups',
        component: () => import('../views/ad/Groups.vue'),
        meta: { title: '安全策略组台账' }
    },
    {
        path: 'ad/logs',
        name: 'ADLogs',
        component: () => import('../views/audit/LogList.vue'),
        meta: { title: '域账号操作日志', module: 'ad' }
    },
    {
        path: 'settings/system',
        name: 'SystemSettings',
        component: () => import('../views/settings/System.vue'),
        meta: { title: '系统设置' }
    },
    {
        path: 'ad/rules',
        name: 'SystemRules',
        component: () => import('../views/ad/Rules.vue'),
        meta: { title: '命名规范' }
    },
    {
        path: 'settings/templates',
        name: 'SystemTemplates',
        component: () => import('../views/settings/Templates.vue'),
        meta: { title: '权限模板配置' }
    },
    {
        path: 'settings/printer',
        name: 'PrinterTemplate',
        component: () => import('../views/settings/PrinterTemplate.vue'),
        meta: { title: '打印模板设置' }
    },
    {
        path: 'inventory/list',
        name: 'InventoryList',
        component: () => import('../views/inventory/InventoryList.vue'),
        meta: { title: '资产盘点控制台' }
    },
    {
        path: 'settings/locations',
        name: 'LocationManagement',
        component: () => import('../views/settings/Locations.vue'),
        meta: { title: '归属地管理' }
    },
    {
        path: 'settings/users',
        name: 'UserManagement',
        component: () => import('../views/settings/Users.vue'),
        meta: { title: '账号与权限分配' }
    }
]

const routes: Array<RouteRecordRaw> = [
    {
        path: '/mobile/asset/create',
        name: 'mobile-asset-create',
        component: () => import('../views/mobile/AssetCreate.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/mobile/asset/:token',
        name: 'mobile-asset-view',
        component: () => import('../views/mobile/AssetView.vue'),
        meta: { title: '移动资产卡片视图', requiresAuth: false }
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/auth/Login.vue'),
        meta: { title: 'ITOM - 管理员登录' }
    },
    // 2. 注入移动端自适应应用中心
    {
        path: '/mobile',
        component: MobileLayout,
        redirect: '/mobile/index',
        children: [
            {
                path: 'index',
                name: 'MobileIndex',
                component: () => import('../views/mobile/Index.vue'),
                meta: { title: '移动端应用中心', requiresAuth: true }
            },
            ...adminRoutes // 动态展开所有路由组件
        ]
    },
    // 3. 桌面端模板
    {
        path: '/',
        component: MainLayout,
        redirect: '/dashboard',
        children: [
            ...adminRoutes as any,
            // 父级菜单默认重定向到第一个子页面，避免右侧空白
            { path: 'assets', redirect: '/assets/list' },
            { path: 'ad', redirect: '/ad/provision' },
            { path: 'settings', redirect: '/settings/templates' }
        ]
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/dashboard'
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation Guard for Authentication
router.beforeEach((to, _from, next) => {
    // Dynamically set page title
    if (to.meta.title) {
        document.title = to.meta.title as string
    }

    const token = localStorage.getItem('itom_token')

    // 允许免登录直接访问的路由 (通过 meta.requiresAuth = false 或是特定的路径前缀)
    const isPublicRoute = to.meta.requiresAuth === false || to.path.startsWith('/mobile/asset/')

    if (to.path !== '/login' && !token && !isPublicRoute) {
        // Redirect to login if not authenticated and not a public route
        next('/login')
    } else if (to.path === '/login' && token) {
        // Redirect to dashboard if already logged in and trying to access login
        next('/dashboard')
    } else {
        next()
    }
})

// Axios Request Interceptor to dynamically attach Token
axios.interceptors.request.use(
    config => {
        const token = localStorage.getItem('itom_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => Promise.reject(error)
)

// Axios Response Interceptor for Global Error Handling (401 Unauthorized)
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            localStorage.removeItem('itom_token')
            delete axios.defaults.headers.common['Authorization']
            router.push('/login')
        }
        return Promise.reject(error)
    }
)

export default router

