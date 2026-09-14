<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'

const list = ref([])
const doctors = ref([])
const loading = ref(false)
const showDialog = ref(false)

/** 新建咨询表单 */
const form = reactive({
  doctor_id: '',
  title: '',
  content: '',
})

/** 加载我的咨询 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/consult/my')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

/** 加载医生列表 */
async function loadDoctors() {
  try {
    const res = await request.get('/doctors/list', { params: { page_size: 100 } })
    doctors.value = parseListData(res)
  } catch {
    doctors.value = []
  }
}

/** 提交咨询 */
async function handleCreate() {
  if (!form.title || !form.content) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await request.post('/consult/create', {
      doctor_id: form.doctor_id,
      chief_complaint: form.title ? `${form.title}：${form.content}` : form.content,
    })
    ElMessage.success('咨询提交成功')
    showDialog.value = false
    Object.assign(form, { doctor_id: '', title: '', content: '' })
    loadList()
  } catch { /* */ }
}

onMounted(() => {
  loadList()
  loadDoctors()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">在线咨询</h2>
      <el-button type="primary" class="gradient-btn" @click="showDialog = true">发起咨询</el-button>
    </div>
    <div class="modern-card">
      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="chief_complaint" label="咨询标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="doctor_name" label="医生" min-width="100" />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'warning'" size="small">
              {{ row.status === 1 ? '已回复' : '待回复' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="提交时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="医生回复" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.replies?.length ? row.replies[row.replies.length - 1].content : '' }}</template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showDialog" title="发起咨询" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="选择医生">
          <el-select v-model="form.doctor_id" placeholder="可不选，由平台统一分诊" clearable style="width:100%">
            <el-option v-for="d in doctors" :key="d.id" :label="d.real_name || d.username" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="咨询标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请描述您的问题" />
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
</style>
