<template>
	<view class="content">
		<view class="header-card">
			<text class="title">ITOM 扫码</text>
			<text class="subtitle">资产流转与管理直达</text>
		</view>

		<view class="btn-group">
			<button class="scan-btn" @click="handleScan">
				<text class="btn-text">调起系统相机扫标签</text>
			</button>
		</view>
		
		<view class="tips">
			<text class="tip-text">原生体验，无需担心HTTPS或摄像头权限遮挡</text>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const handleScan = () => {
	// 调用 uniapp 原生扫码接口
	uni.scanCode({
		success: (res) => {
			let rawValue = res.result
			console.log('Scanned QR:', rawValue)
			
			// 提取 token
			let token = rawValue
			if (rawValue.includes('/asset/')) {
				const parts = rawValue.split('/asset/')
				token = parts[parts.length - 1]
			} else if (rawValue.includes('http')) {
				uni.showToast({
					title: '无法识别外链',
					icon: 'error'
				})
				return
			}
			
			// 跳转到资产卡片页
			uni.navigateTo({
				url: `/pages/asset/index?token=${token}`
			})
		},
		fail: (err) => {
			console.warn('Scan failed', err)
		}
	})
}
</script>

<style>
.content {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 40rpx;
	height: 100vh;
	background-color: #f3f4f6;
}

.header-card {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	margin-top: 100rpx;
	margin-bottom: 120rpx;
	background: #312e81;
	width: 100%;
	padding: 80rpx 0;
	border-radius: 30rpx;
	box-shadow: 0 20rpx 40rpx rgba(49, 46, 129, 0.2);
}

.title {
	font-size: 48rpx;
	color: #ffffff;
	font-weight: bold;
	margin-bottom: 20rpx;
}

.subtitle {
	font-size: 28rpx;
	color: #c7d2fe;
}

.btn-group {
	width: 100%;
	margin-bottom: 60rpx;
}

.scan-btn {
	background: #4f46e5;
	border-radius: 60rpx;
	padding: 10rpx 0;
	display: flex;
	justify-content: center;
	align-items: center;
	box-shadow: 0 10rpx 20rpx rgba(79, 70, 229, 0.3);
}

.btn-text {
	color: white;
	font-size: 32rpx;
	font-weight: bold;
	letter-spacing: 2rpx;
}

.tips {
	margin-top: auto;
	margin-bottom: 40rpx;
}

.tip-text {
	font-size: 24rpx;
	color: #9ca3af;
}
</style>
