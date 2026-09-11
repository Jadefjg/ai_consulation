<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const stats = ref({})

/** 加载工作台数据 */
async function loadStats() {
  try {
    const res = await request.get('/stat/overview')
    stats.value = res.data || {}
  } catch { /* */ }
}

onMounted(loadStats)
</script>

<template>
  <div>
    <h2 class="page-title">医生工作台</h2>
    <el-row :gutter="20">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.pending_consults ?? '--' }}</div>
          <div class="stat-label">待回复咨询</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.overdue_consults ?? '--' }}</div>
          <div class="stat-label">超时咨询</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.today_appointments ?? '--' }}</div>
          <div class="stat-label">今日预约</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_patients ?? '--' }}</div>
          <div class="stat-label">患者总数</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.replied_consults ?? '--' }}</div>
          <div class="stat-label">已回复咨询</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>
