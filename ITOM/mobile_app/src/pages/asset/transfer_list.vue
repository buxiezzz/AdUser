<template>
  <view class="container">
    <view class="tabs">
      <view v-for="(tab, index) in tabList" :key="index" 
            :class="['tab-item', currentTab === index ? 'active' : '']"
            @click="switchTab(index)">
        <text>{{ tab }}</text>
      </view>
    </view>

    <scroll-view scroll-y class="list-area" @scrolltolower="loadMore">
      <view v-for="item in displayedTransfers" :key="item.id" class="transfer-card shadow-sm" @click="viewDetail(item)">
        <view class="card-header">
          <text :class="['status-tag', statusClass(item.status)]">{{ item.status }}</text>
          <text class="time">{{ formatDate(item.created_at) }}</text>
        </view>
        
        <view class="asset-info">
          <text class="code">{{ item.asset?.asset_code || '未知编码' }}</text>
          <text class="category">{{ item.asset?.category?.name || '资产' }}</text>
        </view>

        <view class="route-info">
          <view class="loc">
            <text class="loc-name">{{ item.from_location?.name }}</text>
            <text class="loc-label">起始地</text>
          </view>
          <view class="arrow-wrap">
            <text class="arrow">➔</text>
          </view>
          <view class="loc">
            <text class="loc-name">{{ item.to_location?.name }}</text>
            <text class="loc-label">目的地</text>
          </view>
        </view>

        <view class="card-footer" v-if="canAction(item)">
          <button v-if="isGroupAdmin && item.status === '待审批'" class="action-btn primary" @click.stop="handleApprove(item)">批准</button>
          <button v-if="isGroupAdmin && item.status === '待审批'" class="action-btn danger" @click.stop="handleReject(item)">拒绝</button>
          <button v-if="canShip(item)" class="action-btn warning" @click.stop="handleShip(item)">填写单号发货</button>
          <button v-if="canReceive(item)" class="action-btn success" @click.stop="handleReceive(item)">确认收货签收</button>
        </view>
      </view>

      <view v-if="transfers.length === 0" class="empty">
        <text>暂无调拨记录</text>
      </view>
    </scroll-view>

    <!-- 简易发货弹窗 -->
    <view class="modal-mask" v-if="shipModalVisible" @tap="shipModalVisible = false">
      <view class="modal-content" @tap.stop>
        <view class="modal-header">填写物流单号</view>
        <input class="modal-input" v-model="trackingNumber" placeholder="请输入运单号" />
        <view class="modal-footer">
          <button class="btn-cancel" @tap="shipModalVisible = false">取消</button>
          <button class="btn-confirm" @tap="submitShip">确认发货</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'

const transfers = ref<any[]>([])
const currentTab = ref(0)
const tabList = ['全部', '进行中', '已完成']
const isGroupAdmin = ref(false)
const userLocationId = ref<number | null>(null)

const shipModalVisible = ref(false)
const trackingNumber = ref('')
const currentItem = ref<any>(null)

const displayedTransfers = computed(() => {
  if (currentTab.value === 0) return transfers.value
  if (currentTab.value === 1) return transfers.value.filter(t => ['待审批', '待发货', '运输中'].includes(t.status))
  return transfers.value.filter(t => ['已完成', '已拒绝'].includes(t.status))
})

const fetchTransfers = async () => {
  try {
    const res = await request.get('/transfers/')
    transfers.value = res || []
  } catch (e) {}
}

const fetchUser = async () => {
  try {
    const res = await request.get('/auth/me')
    isGroupAdmin.value = res.is_group_admin
    userLocationId.value = res.location_id
  } catch (e) {}
}

const switchTab = (index: number) => {
  currentTab.value = index
}

const statusClass = (status: string) => {
  if (status === '待审批') return 'status-info'
  if (status === '待发货') return 'status-warning'
  if (status === '运输中') return 'status-primary'
  if (status === '已完成') return 'status-success'
  return 'status-danger'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.replace('T', ' ').substring(0, 16)
}

const canAction = (item: any) => {
  if (isGroupAdmin.value) return true
  if (item.status === '待发货' && item.from_location_id === userLocationId.value) return true
  if (item.status === '运输中' && item.to_location_id === userLocationId.value) return true
  return false
}

const canShip = (item: any) => {
  return item.status === '待发货' && (isGroupAdmin.value || item.from_location_id === userLocationId.value)
}

const canReceive = (item: any) => {
  return item.status === '运输中' && (isGroupAdmin.value || item.to_location_id === userLocationId.value)
}

const handleApprove = (item: any) => {
  uni.showModal({
    title: '审批通过',
    content: '核准申请并进入待发货状态？',
    success: async (res) => {
      if (res.confirm) {
        await request.put(`/transfers/${item.id}`, { status: '待发货' })
        fetchTransfers()
      }
    }
  })
}

const handleReject = (item: any) => {
  uni.showModal({
    title: '拒绝申请',
    editable: true,
    placeholderText: '请输入原因',
    success: async (res) => {
      if (res.confirm) {
        await request.put(`/transfers/${item.id}`, { status: '已拒绝', memo: res.content })
        fetchTransfers()
      }
    }
  })
}

const handleShip = (item: any) => {
  currentItem.value = item
  trackingNumber.value = ''
  shipModalVisible.value = true
}

const submitShip = async () => {
  if (!trackingNumber.value) return uni.showToast({ title: '请输入单号', icon: 'none' })
  await request.put(`/transfers/${currentItem.value.id}`, { 
    status: '运输中', 
    tracking_number: trackingNumber.value 
  })
  shipModalVisible.value = false
  fetchTransfers()
}

const handleReceive = (item: any) => {
  uni.showModal({
    title: '签名确认',
    content: '已收到实物资产并确认无误？',
    success: async (res) => {
      if (res.confirm) {
        await request.put(`/transfers/${item.id}`, { status: '已完成' })
        fetchTransfers()
      }
    }
  })
}

onMounted(() => {
  fetchUser()
  fetchTransfers()
})
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f1f5f9;
}

.tabs {
  display: flex;
  background: #fff;
  padding: 10px 20px;
  position: sticky;
  top: 0;
  z-index: 10;
  
  .tab-item {
    flex: 1;
    text-align: center;
    padding: 10px 0;
    font-size: 15px;
    color: #64748b;
    position: relative;
    
    &.active {
      color: #1a73e8;
      font-weight: bold;
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 30%;
        width: 40%;
        height: 3px;
        background: #1a73e8;
        border-radius: 2px;
      }
    }
  }
}

.list-area {
  flex: 1;
  padding: 15px;
  box-sizing: border-box;
}

.transfer-card {
  background: #fff;
  border-radius: 16px;
  padding: 15px;
  margin-bottom: 15px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
    
    .status-tag {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 6px;
      &.status-info { background: #f1f5f9; color: #64748b; }
      &.status-warning { background: #fff8e1; color: #f59e0b; }
      &.status-primary { background: #eff6ff; color: #3b82f6; }
      &.status-success { background: #ecfdf5; color: #10b981; }
      &.status-danger { background: #fef2f2; color: #ef4444; }
    }
    
    .time { font-size: 12px; color: #94a3b8; }
  }
  
  .asset-info {
    margin-bottom: 15px;
    .code { font-size: 17px; font-weight: bold; color: #1e293b; display: block; }
    .category { font-size: 13px; color: #64748b; }
  }
  
  .route-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 15px;
    
    .loc {
      flex: 1;
      display: flex;
      flex-direction: column;
      .loc-name { font-size: 15px; font-weight: 600; color: #334155; }
      .loc-label { font-size: 11px; color: #94a3b8; margin-top: 2px; }
      &:last-child { text-align: right; }
    }
    
    .arrow-wrap {
      width: 40px;
      text-align: center;
      .arrow { color: #cbd5e1; font-size: 20px; }
    }
  }
  
  .card-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    border-top: 1px solid #f1f5f9;
    padding-top: 12px;
    
    .action-btn {
      margin: 0;
      font-size: 13px;
      height: 32px;
      line-height: 32px;
      padding: 0 15px;
      border-radius: 16px;
      &::after { border: none; }
      
      &.primary { background: #1a73e8; color: #fff; }
      &.danger { background: #fee2e2; color: #ef4444; }
      &.warning { background: #f59e0b; color: #fff; }
      &.success { background: #10b981; color: #fff; }
    }
  }
}

.empty {
  padding: 50px 0;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

.modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: #fff;
  width: 80%;
  border-radius: 16px;
  padding: 20px;
  
  .modal-header { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px; }
  .modal-input {
    background: #f1f5f9;
    height: 48px;
    border-radius: 8px;
    padding: 0 16px;
    margin-bottom: 20px;
    font-size: 16px;
  }
  
  .modal-footer {
    display: flex;
    gap: 15px;
    button {
      flex: 1;
      height: 40px;
      line-height: 40px;
      font-size: 15px;
      border-radius: 20px;
      &::after { border: none; }
    }
    .btn-cancel { background: #f1f5f9; color: #64748b; }
    .btn-confirm { background: #1a73e8; color: #fff; }
  }
}
</style>
