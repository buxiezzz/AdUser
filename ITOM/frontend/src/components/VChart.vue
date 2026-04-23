<template>
  <v-chart class="chart-container" :option="option" :loading="loading" autoresize />
</template>

<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

// Register ECharts modules
use([
  CanvasRenderer,
  PieChart,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent
])

defineProps<{
  option: any
  loading?: boolean
}>()
</script>

<style scoped>
.chart-container {
  height: 100%;
  width: 100%;
  min-height: 300px;
}
</style>
