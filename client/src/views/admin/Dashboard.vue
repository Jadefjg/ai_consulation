<script setup>
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import request from '@/utils/request'

use([CanvasRenderer, LineChart, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const overview = ref({})
const consultTrend = ref({})
const appointmentDept = ref({})
const userGrowth = ref({})
const knowledgeType = ref({})

/** 加载统计数据 */
async function loadStats() {
  try {
    const [ov, ct, ad, ug, kt] = await Promise.allSettled([
      request.get('/stat/overview'),
      request.get('/stat/consult-trend'),
      request.get('/stat/appointment-dept'),
      request.get('/stat/user-growth'),
      request.get('/stat/knowledge-type'),
    ])
    if (ov.status === 'fulfilled') overview.value = ov.value.data || {}
    if (ct.status === 'fulfilled') consultTrend.value = buildLineOption('咨询趋势', ct.value.data)
    if (ad.status === 'fulfilled') appointmentDept.value = buildPieOption('预约科室分布', ad.value.data)
    if (ug.status === 'fulfilled') userGrowth.value = buildBarOption('用户增长', ug.value.data)
    if (kt.status === 'fulfilled') knowledgeType.value = buildPieOption('知识库类型', kt.value.data)
  } catch { /* */ }
}

/** 构建折线图配置 */
function buildLineOption(title, data) {
  const items = data?.items || data?.list || data || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: items.map((i) => i.date || i.label || i.name) },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      smooth: true,
      data: items.map((i) => i.count || i.value || 0),
      areaStyle: { color: 'rgba(102,126,234,0.15)' },
      lineStyle: { color: '#667eea', width: 3 },
      itemStyle: { color: '#667eea' },
    }],
  }
}

/** 构建饼图配置 */
function buildPieOption(title, data) {
  const items = data?.items || data?.list || data || []
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      data: items.map((i) => ({ name: i.name || i.label, value: i.count || i.value || 0 })),
      emphasis: { itemStyle: { shadowBlur: 10 } },
    }],
  }
}

/** 构建柱状图配置 */
function buildBarOption(title, data) {
  const items = data?.items || data?.list || data || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: items.map((i) => i.date || i.label || i.name) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: items.map((i) => i.count || i.value || 0),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
          { offset: 0, color: '#667eea' }, { offset: 1, color: '#764ba2' },
        ]},
      },
    }],
  }
}

onMounted(loadStats)
</script>

<template>
  <div>
    <h2 class="page-title">数据概览</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ overview.user_count ?? '--' }}</div>
          <div class="stat-label">用户总数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ overview.doctor_count ?? '--' }}</div>
          <div class="stat-label">医生总数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ overview.consult_count ?? '--' }}</div>
          <div class="stat-label">咨询总数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ overview.appointment_count ?? '--' }}</div>
          <div class="stat-label">预约总数</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="chart-box">
          <div class="chart-title">咨询趋势</div>
          <v-chart :option="consultTrend" autoresize style="height:280px" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="chart-box">
          <div class="chart-title">预约科室分布</div>
          <v-chart :option="appointmentDept" autoresize style="height:280px" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="chart-box">
          <div class="chart-title">用户增长</div>
          <v-chart :option="userGrowth" autoresize style="height:280px" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="chart-box">
          <div class="chart-title">知识库类型</div>
          <v-chart :option="knowledgeType" autoresize style="height:280px" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-row {
  margin-bottom: 24px;
}

.chart-box {
  margin-bottom: 20px;
}
</style>
