<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const list = ref([])
const loading = ref(false)
const patientOptions = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

/** 档案类型选项 */
const recordTypeOptions = ['门诊记录', '住院记录', '体检报告', '复诊记录', '其他']

/** 表单默认值 */
const defaultForm = () => ({
  id: null,
  user_id: null,
  record_type: '门诊记录',
  diagnosis: '',
  treatment: '',
  prescription: '',
  visit_date: '',
})

const form = ref(defaultForm())

/** 加载患者档案 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/records/doctor/patients')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

/** 加载可选患者 */
async function loadPatientOptions() {
  try {
    const res = await request.get('/records/doctor/patient-options')
    patientOptions.value = res.data || []
  } catch {
    patientOptions.value = []
  }
}

/** 打开新增对话框 */
function openCreate() {
  isEdit.value = false
  form.value = defaultForm()
  dialogVisible.value = true
}

/** 打开编辑对话框 */
function openEdit(row) {
  isEdit.value = true
  form.value = {
    id: row.id,
    user_id: row.user_id,
    record_type: row.record_type || '门诊记录',
    diagnosis: row.diagnosis || '',
    treatment: row.treatment || '',
    prescription: row.prescription || '',
    visit_date: row.visit_date || '',
  }
  dialogVisible.value = true
}

/** 提交表单 */
async function submitForm() {
  if (!isEdit.value && !form.value.user_id) {
    ElMessage.warning('请选择患者')
    return
  }
  if (!form.value.record_type) {
    ElMessage.warning('请选择档案类型')
    return
  }
  submitting.value = true
  try {
    const payload = {
      record_type: form.value.record_type,
      diagnosis: form.value.diagnosis,
      treatment: form.value.treatment,
      prescription: form.value.prescription,
      visit_date: form.value.visit_date || null,
    }
    if (isEdit.value) {
      await request.put(`/records/doctor/${form.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/records/doctor/create', {
        user_id: form.value.user_id,
        ...payload,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
    loadPatientOptions()
  } catch { /* */ } finally {
    submitting.value = false
  }
}

/** 删除档案 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除患者「${row.user_name}」的档案吗？`, '提示', { type: 'warning' })
    await request.delete(`/records/doctor/${row.id}`)
    ElMessage.success('删除成功')
    loadList()
  } catch { /* */ }
}

onMounted(() => {
  loadList()
  loadPatientOptions()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">患者档案</h2>
      <el-button type="primary" @click="openCreate">新增档案</el-button>
    </div>
    <div class="modern-card">
      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="user_name" label="患者姓名" min-width="100" />
        <el-table-column prop="record_type" label="档案类型" min-width="120" />
        <el-table-column prop="diagnosis" label="诊断" min-width="180" show-overflow-tooltip />
        <el-table-column prop="treatment" label="治疗方案" min-width="180" show-overflow-tooltip />
        <el-table-column prop="visit_date" label="就诊日期" min-width="120" />
        <el-table-column prop="create_time" label="记录时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="暂无患者档案" />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑档案' : '新增档案'"
      width="560px"
      destroy-on-close
    >
      <el-form label-width="90px">
        <el-form-item label="患者" required>
          <el-select
            v-if="!isEdit"
            v-model="form.user_id"
            placeholder="请选择患者"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="item in patientOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
          <el-input v-else :model-value="list.find(i => i.id === form.id)?.user_name" disabled />
        </el-form-item>
        <el-form-item label="档案类型" required>
          <el-select v-model="form.record_type" placeholder="请选择档案类型" style="width: 100%">
            <el-option v-for="item in recordTypeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="诊断">
          <el-input v-model="form.diagnosis" placeholder="请输入诊断结果" />
        </el-form-item>
        <el-form-item label="治疗方案">
          <el-input v-model="form.treatment" type="textarea" :rows="3" placeholder="请输入治疗方案" />
        </el-form-item>
        <el-form-item label="处方">
          <el-input v-model="form.prescription" type="textarea" :rows="2" placeholder="请输入处方（选填）" />
        </el-form-item>
        <el-form-item label="就诊日期">
          <el-date-picker
            v-model="form.visit_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择就诊日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header .page-title {
  margin-bottom: 0;
}
</style>
