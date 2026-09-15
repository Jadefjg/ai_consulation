<script setup lang="ts">
import { computed, ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'

const list = ref([])
const departments = ref([])
const doctors = ref([])
const availableSchedules = ref([])
const loading = ref(false)
const scheduleLoading = ref(false)
const showDialog = ref(false)

const availableDates = computed(() => new Set(availableSchedules.value.map(item => item.date)))
const timeSlotOptions = computed(() => availableSchedules.value.filter(
  item => item.date === form.visit_date,
))
const selectedDateConflict = computed(() => (
  timeSlotOptions.value.length > 0 && timeSlotOptions.value.every(item => !item.bookable)
))

/** 仅允许选择当前医生存在剩余号源的日期 */
function disableUnavailableDate(date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (date < today) return true
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return !availableDates.value.has(`${year}-${month}-${day}`)
}

/** 预约状态映射 */
const statusMap = {
  0: '待确认',
  1: '已确认',
  2: '已完成',
  3: '已取消',
}

/** 预约表单（字段名与后端接口一致） */
const form = reactive({
  doctor_id: '',
  department_id: '',
  visit_date: '',
  time_slot: '',
  remark: '',
})

/** 重置预约表单 */
function resetForm() {
  form.doctor_id = ''
  form.department_id = ''
  form.visit_date = ''
  form.time_slot = ''
  form.remark = ''
  availableSchedules.value = []
}

/** 加载预约列表 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/appointments/my')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

/** 加载科室列表 */
async function loadDepartments() {
  try {
    const deptRes = await request.get('/departments/list')
    departments.value = deptRes.data || []
  } catch { /* */ }
}

/** 加载医生列表（可按科室筛选） */
async function loadDoctors(departmentId) {
  try {
    const params = { page_size: 100 }
    if (departmentId) params.department_id = departmentId
    const docRes = await request.get('/doctors/list', { params })
    doctors.value = parseListData(docRes)
  } catch {
    doctors.value = []
  }
}

/** 加载医生真实可用排班及剩余号源 */
async function loadAvailableSchedules(doctorId) {
  availableSchedules.value = []
  form.visit_date = ''
  form.time_slot = ''
  if (!doctorId) return
  scheduleLoading.value = true
  try {
    const res = await request.get('/appointments/available-schedules', {
      params: { doctor_id: doctorId },
    })
    availableSchedules.value = res.data || []
  } catch {
    availableSchedules.value = []
  } finally {
    scheduleLoading.value = false
  }
}

/** 打开新建预约弹窗 */
function openDialog() {
  resetForm()
  showDialog.value = true
  loadDoctors()
}

/** 取消预约 */
async function handleCancel(row) {
  try {
    await request.put(`/appointments/my/${row.id}/cancel`)
    ElMessage.success('预约已取消')
    loadList()
  } catch { /* */ }
}

/** 提交预约 */
async function handleCreate() {
  if (!form.department_id || !form.doctor_id || !form.visit_date || !form.time_slot) {
    ElMessage.warning('请填写科室、医生、预约日期和时段')
    return
  }
  try {
    await request.post('/appointments/create', {
      doctor_id: form.doctor_id,
      department_id: form.department_id,
      visit_date: form.visit_date,
      time_slot: form.time_slot,
      remark: form.remark || undefined,
    })
    ElMessage.success('预约成功')
    showDialog.value = false
    resetForm()
    loadList()
  } catch { /* */ }
}

/** 科室变更时重新加载对应医生 */
watch(() => form.department_id, (val) => {
  form.doctor_id = ''
  availableSchedules.value = []
  loadDoctors(val || undefined)
})

watch(() => form.doctor_id, (val) => loadAvailableSchedules(val || undefined))
watch(() => form.visit_date, () => { form.time_slot = '' })

onMounted(() => {
  loadList()
  loadDepartments()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">预约挂号</h2>
      <el-button type="primary" class="gradient-btn" @click="openDialog">新建预约</el-button>
    </div>
    <div class="modern-card">
      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="doctor_name" label="医生" min-width="100" />
        <el-table-column prop="department_name" label="科室" min-width="120" />
        <el-table-column prop="visit_date" label="预约日期" min-width="120" />
        <el-table-column prop="time_slot" label="时段" min-width="80" />
        <el-table-column prop="remark" label="预约原因" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ statusMap[row.status] ?? '待确认' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 0 || row.status === 1"
              type="danger"
              link
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showDialog" title="新建预约" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="科室">
          <el-select v-model="form.department_id" placeholder="选择科室" style="width:100%">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="医生">
          <el-select v-model="form.doctor_id" placeholder="选择医生" style="width:100%">
            <el-option v-for="d in doctors" :key="d.id" :label="d.real_name || d.username" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="预约日期">
          <el-date-picker
            v-model="form.visit_date"
            type="date"
            value-format="YYYY-MM-DD"
            :disabled="!form.doctor_id || scheduleLoading"
            :disabled-date="disableUnavailableDate"
            placeholder="请选择有号日期"
            style="width:100%"
          />
          <div v-if="form.doctor_id && !scheduleLoading && !availableSchedules.length" class="schedule-hint">
            该医生暂无可预约排班
          </div>
        </el-form-item>
        <el-form-item label="时段">
          <el-select v-model="form.time_slot" :disabled="!form.visit_date" placeholder="选择时段" style="width:100%">
            <el-option
              v-for="slot in timeSlotOptions"
              :key="slot.time_slot"
              :label="slot.bookable ? `${slot.time_slot}（剩余 ${slot.remaining}）` : `${slot.time_slot}（您已有预约）`"
              :value="slot.time_slot"
              :disabled="!slot.bookable"
            />
          </el-select>
          <div v-if="selectedDateConflict" class="schedule-hint">
            您在该日期的可用时段已有待处理预约；如需改约，请先在预约列表中取消原预约。
          </div>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请简要描述预约原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" class="gradient-btn" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.text-muted {
  color: #c0c4cc;
}

.schedule-hint {
  color: #e6a23c;
  font-size: 12px;
  line-height: 20px;
}
</style>
