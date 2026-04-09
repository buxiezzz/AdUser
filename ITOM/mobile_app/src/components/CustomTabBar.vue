<template>
  <view class="custom-tabbar-container">
    <view class="tabbar-border"></view>
    <view class="tabbar-main">
      <view 
        v-for="(item, index) in tabList" 
        :key="index" 
        class="tab-item"
        :class="{ 'active': activeIndex === index, 'is-center': index === 2 }"
        @click="switchTab(index, item.pagePath)"
      >
        <view class="icon-box" :class="{ 'center-icon': index === 2 }">
          <text class="icon-emoji">{{ getIcon(index, activeIndex === index) }}</text>
        </view>
        <text class="tab-label">{{ item.text }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  activeIndex: number
}>()

const tabList = [
  { pagePath: '/pages/index/index', text: '首页' },
  { pagePath: '/pages/asset/list', text: '资产' },
  { pagePath: '/pages/scan/index', text: '扫描资产' },
  { pagePath: '/pages/inventory/index', text: '盘点' },
  { pagePath: '/pages/settings/index', text: '设置' }
]

const getIcon = (index: number, isActive: boolean) => {
  const icons = ['🏠', '📦', '📷', '📋', '⚙️']
  return icons[index]
}

const switchTab = (index: number, url: string) => {
  if (props.activeIndex === index) return
  uni.switchTab({
    url,
    fail: () => {
      uni.navigateTo({ url })
    }
  })
}
</script>

<style lang="scss" scoped>
.custom-tabbar-container {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  z-index: 999;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(15px);
  padding-bottom: calc(12px + env(safe-area-inset-bottom)); /* 极大地增加底部安全距离 */
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.08);
}

.tabbar-main {
  display: flex;
  height: 75px; /* 增加物理高度 */
  align-items: center;
  position: relative;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  
  &:active {
    transform: scale(0.9);
    opacity: 0.7;
  }
}

.icon-box {
  font-size: 28px; /* 图标加大 */
  margin-bottom: 4px;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.tab-label {
  font-size: 11px;
  color: #555; /* 加深颜色，更清晰 */
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
}

.active {
  .icon-box {
    transform: translateY(-2px);
  }
  .tab-label {
    color: #1677ff;
    font-weight: 800; /* 选中时加粗 */
  }
}

/* 中间突出的扫描按钮 */
.is-center {
  position: relative;
  
  .center-icon {
    width: 62px;
    height: 62px;
    background: linear-gradient(135deg, #1677ff, #4fa3ff);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 38px;
    box-shadow: 0 5px 18px rgba(22, 119, 255, 0.45);
    border: 4px solid #fff;
    font-size: 32px; /* 进一步加大 */
  }
  
  .tab-label {
    position: absolute;
    bottom: 12px; /* 文字显著上提，远离屏幕边缘 */
    font-weight: 800;
    color: #1677ff;
    font-size: 11px;
    width: 100px;
  }
}

.icon-emoji {
  line-height: 1;
}
</style>
