<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const list = ref([])
const loading = ref(false)

/** 预约状态映射 */
const statusMap = {
  0: '待确认',
  1: '已确认',
  2: '已完成',
  3: '已取消',
}

/** 预约状态标签样式 */
const statusTypeMap = {
  0: 'warning',
  1: 'success',
  2: 'info',
  3: 'danger',
}

/** 加载医生预约 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/appointments/doctor/my')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

/** 更新预约状态 */
async function updateStatus(row, status, actionText) {
  try {
    await ElMessageBox.confirm(`确定要${actionText}该预约吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await request.put(`/appointments/${row.id}/status`, null, { params: { status } })
    ElMessage.success(`${actionText}成功`)
    loadList()
  } catch { /* 用户取消或请求失败 */ }
}

onMounted(loadList)
</script>

<template>
  <div>
    <h2 class="page-title">我的预约</h2>
    <div class="modern-card">
      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="user_name" label="患者" min-width="100" />
        <el-table-column prop="visit_date" label="预约日期" min-width="120" />
        <el-table-column prop="time_slot" label="时段" min-width="80" />
        <el-table-column prop="remark" label="预约原因" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="statusTypeMap[row.status] || 'warning'" size="small">
              {{ statusMap[row.status] ?? '待确认' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 0"
              link
              type="primary"
              @click="updateStatus(row, 1, '确认')"
            >
              确认
            </el-button>
            <el-button
              v-if="row.status === 1"
              link
              type="success"
              @click="updateStatus(row, 2, '完成')"
            >
              完成
            </el-button>
            <el-button
              v-if="row.status === 0 || row.status === 1"
              link
              type="danger"
              @click="updateStatus(row, 3, '取消')"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
