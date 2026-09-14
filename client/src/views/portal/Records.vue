<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const list = ref([])
const loading = ref(false)

/** 加载健康档案 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/records/my')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadList)
</script>

<template>
  <div>
    <h2 class="page-title">健康档案</h2>
    <div class="modern-card">
      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="record_type" label="档案类型" min-width="120" />
        <el-table-column prop="diagnosis" label="诊断" min-width="180" show-overflow-tooltip />
        <el-table-column prop="treatment" label="治疗方案" min-width="180" show-overflow-tooltip />
        <el-table-column prop="doctor_name" label="主治医生" min-width="100" />
        <el-table-column prop="visit_date" label="就诊日期" min-width="120" />
        <el-table-column prop="create_time" label="记录时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="暂无健康档案" />
    </div>
  </div>
</template>
