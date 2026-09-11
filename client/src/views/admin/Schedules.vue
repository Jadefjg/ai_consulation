<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { parseListData } from '@/utils/format'
const doctors = ref([])
const loading = ref(false)
const submitting = ref(false)
const schedules = ref([])
const timeSlotOptions = ['上午', '下午', '晚上']
const form = ref({ doctor_id: '', work_date: '', time_slot: '', capacity: 1 })

async function load() {
  loading.value = true
  try {
    const r = await request.get('/doctors/list', { params: { page_size: 100 } })
    // Keep select values consistent with the string form model so labels remain
    // resolvable after Element Plus updates the option list.
    doctors.value = parseListData(r).map((doctor) => ({
      ...doctor,
      id: String(doctor.id),
      real_name: doctor.real_name || doctor.username || `医生 ${doctor.id}`,
    }))
  } catch {
    doctors.value = []
  } finally {
    loading.value = false
  }
}

async function loadSchedules() {
  try {
    const response = await request.get('/appointments/admin/schedules')
    schedules.value = parseListData(response)
  } catch {
    schedules.value = []
  }
}

async function submit() {
  if (!form.value.doctor_id || !form.value.work_date) return ElMessage.warning('请选择医生和日期')
  submitting.value = true
  try {
    await request.post('/appointments/admin/schedules', null, {
      params: { ...form.value, doctor_id: Number(form.value.doctor_id) },
    })
    ElMessage.success('排班创建成功')
    await loadSchedules()
  } finally {
    submitting.value = false
  }
}
onMounted(() => {
  load()
  loadSchedules()
})
</script>
<template>
  <div>
    <h2 class="page-title">医生排班与号源</h2>
    <div class="modern-card">
      <el-form inline class="schedule-form">
        <el-form-item label="医生">
          <el-select v-model="form.doctor_id" placeholder="请选择医生" :loading="loading" filterable>
            <el-option v-for="doctor in doctors" :key="doctor.id" :value="doctor.id" :label="doctor.real_name" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="form.work_date" value-format="YYYY-MM-DD" type="date" placeholder="请选择日期" />
        </el-form-item>
        <el-form-item label="时段">
          <el-select v-model="form.time_slot" placeholder="请选择时段" class="time-slot-select">
            <el-option v-for="slot in timeSlotOptions" :key="slot" :value="slot" :label="slot" />
          </el-select>
        </el-form-item>
        <el-form-item label="号源">
          <el-input-number v-model="form.capacity" :min="1" :max="100" />
        </el-form-item>
        <el-form-item class="schedule-submit">
          <el-button type="primary" :loading="submitting" @click="submit">创建排班</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div class="modern-card schedule-list">
      <el-table :data="schedules" v-loading="loading" stripe>
        <el-table-column prop="doctor_name" label="医生" min-width="140" />
        <el-table-column prop="work_date" label="日期" min-width="130" />
        <el-table-column prop="time_slot" label="时段" min-width="100" />
        <el-table-column prop="capacity" label="号源" min-width="90" />
        <el-table-column label="状态" min-width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!schedules.length" description="暂无排班数据" />
    </div>
  </div>
</template>

<style scoped>
.schedule-form {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 18px;
}

.schedule-form :deep(.el-form-item) {
  margin-right: 0;
  margin-bottom: 0;
  flex: 0 0 auto;
}

.schedule-submit {
  margin-left: 2px;
}

.time-slot-select {
  width: 110px;
}

@media (max-width: 900px) {
  .schedule-form {
    flex-wrap: wrap;
  }
}
</style>
