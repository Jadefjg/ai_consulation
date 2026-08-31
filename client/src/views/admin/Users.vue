<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

/** 表单默认值 */
const defaultForm = () => ({
  id: null,
  username: '',
  password: '',
  confirm_password: '',
  real_name: '',
  gender: 1,
  age: null,
  phone: '',
  allergy_history: '',
  status: 1,
})

const form = ref(defaultForm())

/** 加载用户列表 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/users/list', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        keyword: keyword.value.trim(),
      },
    })
    list.value = parseListData(res)
    total.value = res.data?.total ?? list.value.length
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** 搜索用户 */
function handleSearch() {
  page.value = 1
  loadList()
}

/** 重置搜索 */
function handleReset() {
  keyword.value = ''
  page.value = 1
  loadList()
}

/** 分页切换 */
function handlePageChange(p) {
  page.value = p
  loadList()
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
    username: row.username,
    password: '',
    confirm_password: '',
    real_name: row.real_name || '',
    gender: row.gender ?? 1,
    age: row.age ?? null,
    phone: row.phone || '',
    allergy_history: row.allergy_history || '',
    status: row.status ?? 1,
  }
  dialogVisible.value = true
}

/** 提交表单 */
async function submitForm() {
  if (!isEdit.value) {
    if (!form.value.username?.trim()) {
      ElMessage.warning('请输入用户名')
      return
    }
    if (form.value.username.trim().length < 3) {
      ElMessage.warning('用户名至少3个字符')
      return
    }
    if (!form.value.password) {
      ElMessage.warning('请输入密码')
      return
    }
    if (form.value.password.length < 6) {
      ElMessage.warning('密码至少6个字符')
      return
    }
    if (form.value.password !== form.value.confirm_password) {
      ElMessage.warning('两次密码输入不一致')
      return
    }
  } else if (form.value.password) {
    if (form.value.password.length < 6) {
      ElMessage.warning('密码至少6个字符')
      return
    }
    if (form.value.password !== form.value.confirm_password) {
      ElMessage.warning('两次密码输入不一致')
      return
    }
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      const payload = {
        real_name: form.value.real_name,
        gender: form.value.gender,
        age: form.value.age,
        phone: form.value.phone,
        allergy_history: form.value.allergy_history,
        status: form.value.status,
      }
      if (form.value.password) {
        payload.password = form.value.password
        payload.confirm_password = form.value.confirm_password
      }
      await request.put(`/users/${form.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/users/create', {
        username: form.value.username.trim(),
        password: form.value.password,
        confirm_password: form.value.confirm_password,
        real_name: form.value.real_name,
        gender: form.value.gender,
        age: form.value.age,
        phone: form.value.phone,
        allergy_history: form.value.allergy_history,
        status: form.value.status,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch { /* */ } finally {
    submitting.value = false
  }
}

/** 删除用户 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${row.username}」吗？删除后相关问诊、预约等数据也将一并清除。`,
      '提示',
      { type: 'warning' },
    )
    await request.delete(`/users/${row.id}`)
    ElMessage.success('删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    loadList()
  } catch { /* */ }
}

/** 切换用户状态 */
async function toggleStatus(row) {
  const newStatus = row.status === 1 ? 0 : 1
  const action = newStatus === 1 ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定${action}用户「${row.username}」吗？`, '提示', { type: 'warning' })
    await request.put(`/users/${row.id}/status`, null, { params: { status: newStatus } })
    ElMessage.success(`${action}成功`)
    loadList()
  } catch { /* */ }
}

onMounted(loadList)
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>

    <div class="modern-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索用户名 / 昵称 / 手机号"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="real_name" label="用户昵称" min-width="100" />
        <el-table-column prop="gender" label="性别" min-width="70">
          <template #default="{ row }">
            {{ row.gender === 2 ? '女' : '男' }}
          </template>
        </el-table-column>
        <el-table-column prop="age" label="年龄" min-width="70" />
        <el-table-column prop="role_label" label="角色" min-width="90">
          <template #default="{ row }">
            <el-tag
              :type="row.role === 'root' ? 'danger' : row.role === 'admin' ? 'danger' : row.role === 'doctor' ? 'warning' : 'primary'"
              size="small"
            >
              {{ row.role_label || '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="130" />
        <el-table-column prop="status" label="状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.role === 'user'">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">
                {{ row.status === 1 ? '禁用' : '启用' }}
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
            <span v-else class="role-hint">
              {{ row.role === 'root' ? '超级管理员账号' : `请在「${row.role === 'doctor' ? '医生' : '管理员'}管理」中操作` }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !list.length" description="暂无用户数据" />

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="560px"
      destroy-on-close
    >
      <el-form label-width="90px">
        <el-form-item label="用户名" required>
          <el-input
            v-if="!isEdit"
            v-model="form.username"
            placeholder="请输入用户名"
            maxlength="50"
          />
          <el-input v-else :model-value="form.username" disabled />
        </el-form-item>
        <el-form-item :label="isEdit ? '新密码' : '密码'" :required="!isEdit">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="isEdit ? '不修改请留空' : '请输入密码'"
          />
        </el-form-item>
        <el-form-item :label="isEdit ? '确认新密码' : '确认密码'" :required="!isEdit">
          <el-input
            v-model="form.confirm_password"
            type="password"
            show-password
            :placeholder="isEdit ? '不修改请留空' : '请再次输入密码'"
          />
        </el-form-item>
        <el-form-item label="用户昵称">
          <el-input v-model="form.real_name" placeholder="请输入用户昵称" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="1" :max="150" controls-position="right" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" maxlength="20" />
        </el-form-item>
        <el-form-item label="过敏史">
          <el-input
            v-model="form.allergy_history"
            type="textarea"
            :rows="2"
            placeholder="请输入过敏史（选填）"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
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
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.role-hint {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
