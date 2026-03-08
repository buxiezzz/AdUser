import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import axios from 'axios'

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
        path: '/mobile/scan',
        name: 'mobile-asset-scan',
        component: () => import('../views/mobile/Scan.vue'),
        meta: { title: '扫一扫', requiresAuth: false }
    },
    {
        path: '/mobile/home',
        name: 'mobile-home',
        component: () => import('../views/mobile/Home.vue'),
        meta: { title: 'ITOM 移动端', requiresAuth: false }
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/auth/Login.vue'),
        meta: { title: 'ITOM - 管理员登录' }
    },
    {
        path: '/',
        component: MainLayout,
        redirect: '/dashboard',
        children: [
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
                path: 'ad/provision',
                name: 'ADProvision',
                component: () => import('../views/ad/Provision.vue'),
                meta: { title: '域用户开通向导' }
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
                meta: { title: '安全组策略' }
            },
            {
                path: 'settings/system',
                name: 'SystemSettings',
                component: () => import('../views/settings/System.vue'),
                meta: { title: '系统底座配置' }
            },
            {
                path: 'settings/rules',
                name: 'SystemRules',
                component: () => import('../views/settings/Rules.vue'),
                meta: { title: '命名规范中心' }
            },
            {
                path: 'settings/templates',
                name: 'SystemTemplates',
                component: () => import('../views/settings/Templates.vue'),
                meta: { title: '权限模板配置' }
            }
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
    const forcePc = sessionStorage.getItem('itom_force_pc') === '1'
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

    // 允许免登录直接访问的路由
    const isPublicRoute = to.meta.requiresAuth === false || to.path.startsWith('/mobile/asset/') || to.path === '/mobile/home'

    // Device specific routing for root or login
    if (isMobile && !forcePc && (to.path === '/login' || to.path === '/')) {
        window.location.href = window.location.origin.replace(':5173', ':5174') + '/'
        return
    }

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

