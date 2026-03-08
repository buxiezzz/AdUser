<template>
	<view class="container">
		<view v-if="loading" class="loading">
			<text>正在加载资产信息...</text>
		</view>
		<view v-else-if="error" class="error">
			<text>{{ error }}</text>
		</view>
		<view v-else-if="asset" class="card">
			<view class="header">
				<text class="title">{{ categoryName }}</text>
                <text class="status">{{ asset.status }}</text>
            </view>
			<view class="code">
                <text>{{ asset.asset_code }}</text>
			</view>
			
			<view class="section">
                <view class="section-title">所属信息</view>
                <view class="item">
                    <text class="label">使用人</text>
                    <text class="value">{{ ownerName }}</text>
                </view>
                <view class="item">
                    <text class="label">部门</text>
                    <text class="value">{{ department }}</text>
                </view>
			</view>

            <view class="section" v-if="dynamics.length > 0">
                <view class="section-title">详细参数</view>
                <view class="item" v-for="d in dynamics" :key="d.key">
                    <text class="label">{{ d.key }}</text>
                    <text class="value">{{ d.val }}</text>
                </view>
            </view>

		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const loading = ref(true)
const error = ref('')
const asset = ref<any>(null)

// 你的后台API地址。如果你用真机测试，请确保填写运行后台的电脑IP，而不是127.0.0.1
const API_BASE = 'http://192.168.110.15:8000'

onLoad((options: any) => {
	const token = options.token
	if (!token) {
		error.value = '未获取到Token'
		loading.value = false
		return
	}
	fetchData(token)
})

const fetchData = (token: string) => {
	uni.request({
		url: `${API_BASE}/api/assets/mobile/${token}`,
		method: 'GET',
		success: (res: any) => {
			if(res.statusCode === 200) {
				asset.value = res.data
			} else {
				error.value = res.data.detail || '获取失败'
			}
		},
		fail: () => {
			error.value = '网络请求失败'
		},
		complete: () => {
			loading.value = false
		}
	})
}

const categoryName = computed(() => {
	return asset.value?.category?.name || '未知资产'
})

const ownerName = computed(() => {
    return asset.value?.owner?.name || '闲置中'
})

const department = computed(() => {
    return asset.value?.owner?.department || '-'
})

const dynamics = computed(() => {
    if(!asset.value?.dynamic_attributes) return []
    const arr = []
    for (const key in asset.value.dynamic_attributes) {
        if (asset.value.dynamic_attributes[key]) {
            arr.push({ key, val: asset.value.dynamic_attributes[key] })
        }
    }
    return arr
})
</script>

<style>
.container {
	padding: 30rpx;
	background-color: #f3f4f6;
	min-height: 100vh;
}

.loading, .error {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 400rpx;
	color: #6b7280;
}

.error {
    color: #ef4444;
}

.card {
	background-color: white;
	border-radius: 20rpx;
	padding: 40rpx;
	box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.05);
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	border-bottom: 2rpx solid #f3f4f6;
	padding-bottom: 20rpx;
	margin-bottom: 10rpx;
}

.title {
	font-size: 40rpx;
	font-weight: bold;
	color: #1f2937;
}

.status {
    background-color: #d1fae5;
    color: #059669;
    padding: 6rpx 20rpx;
    border-radius: 30rpx;
    font-size: 24rpx;
    font-weight: bold;
}

.code {
    font-size: 24rpx;
    color: #9ca3af;
    font-family: monospace;
    margin-bottom: 40rpx;
}

.section {
    margin-bottom: 40rpx;
}

.section-title {
    font-size: 30rpx;
    color: #6b7280;
    margin-bottom: 20rpx;
    font-weight: bold;
}

.item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16rpx;
}

.label {
    color: #6b7280;
    font-size: 28rpx;
}

.value {
    color: #1f2937;
    font-size: 28rpx;
    font-weight: bold;
    text-align: right;
    max-width: 60%;
}
</style>
