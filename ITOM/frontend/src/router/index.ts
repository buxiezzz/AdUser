import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import axios from 'axios'

const routes: Array<RouteRecordRaw> = [
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

    if (to.path !== '/login' && !token) {
        // Redirect to login if not authenticated
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

