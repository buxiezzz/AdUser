import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
    {
        path: '/',
        name: 'Home',
        component: () => import('../views/Home.vue'),
        meta: { title: 'ITOM 移动端' }
    },
    {
        path: '/scan',
        name: 'Scan',
        component: () => import('../views/Scan.vue'),
        meta: { title: '扫一扫' }
    },
    {
        path: '/asset/:token',
        name: 'AssetView',
        component: () => import('../views/AssetView.vue'),
        meta: { title: '移动资产卡片视图' }
    },
    {
        path: '/asset/create',
        name: 'AssetCreate',
        component: () => import('../views/AssetCreate.vue'),
        meta: { title: '资产录入' }
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, _from, next) => {
    if (to.meta.title) {
        document.title = to.meta.title as string
    }
    next()
})

export default router
