<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const list = ref([])
const loading = ref(false)
const replyDialog = ref(false)
const currentItem = ref(null)
const replyText = ref('')

/** 解析主诉为标题与咨询内容（格式：标题：内容） */
function parseComplaint(chiefComplaint) {
  const text = chiefComplaint || ''
  const idx = text.indexOf('：')
  if (idx > 0) {
    return { title: text.slice(0, idx), content: text.slice(idx + 1) }
  }
  return { title: text, content: '' }
}

/** 加载待回复咨询 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/consult/doctor/pending')
    list.value = res.data || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

/** 打开回复对话框 */
function openReply(row) {
  currentItem.value = row
  replyText.value = ''
  replyDialog.value = true
}

/** 提交回复 */
async function submitReply() {
  if (!replyText.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  try {
    await request.post('/consult/reply', {
      consult_id: currentItem.value.id,
      content: replyText.value,
    })
    ElMessage.success('回复成功')
    replyDialog.value = false
    loadList()
  } catch { /* */ }
}

onMounted(loadList)
</script>

<template>
  <div>
    <h2 class="page-title">待回复咨询</h2>
    <div class="modern-card">
      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column label="标题" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ parseComplaint(row.chief_complaint).title }}</template>
        </el-table-column>
        <el-table-column prop="user_name" label="患者" min-width="100" />
        <el-table-column label="咨询内容" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ parseComplaint(row.chief_complaint).content }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="提交时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openReply(row)">回复</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="replyDialog" title="回复咨询" width="520px">
      <el-input v-model="replyText" type="textarea" :rows="5" placeholder="请输入回复内容" />
      <template #footer>
        <el-button @click="replyDialog = false">取消</el-button>
        <el-button type="primary" class="gradient-btn" @click="submitReply">提交回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>
