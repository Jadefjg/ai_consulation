<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'
import { useUserStore } from '@/stores/user'
import AppPagination from '@/components/AppPagination.vue'

const userStore = useUserStore()
const isRoot = computed(() => userStore.role === 'root')

const list = ref([])
const departments = ref([])
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
  role: 'user',
  username: '',
  password: '',
  confirm_password: '',
  real_name: '',
  gender: 1,
  age: null,
  phone: '',
  email: '',
  allergy_history: '',
  department_id: null,
  title: '',
  specialty: '',
  introduction: '',
  status: 1,
})

const form = ref(defaultForm())

/** 是否可管理该行账号 */
function canManage(row) {
  if (row.role === 'root') return false
  if (isRoot.value) return ['user', 'doctor', 'admin'].includes(row.role)
  return row.role === 'user'
}

/** 接口前缀 */
function apiPrefix(role) {
  if (role === 'doctor') return '/doctors'
  if (role === 'admin') return '/admins'
  return '/users'
}

/** 角色显示名 */
function roleLabel(role) {
  return { user: '用户', doctor: '医生', admin: '管理员' }[role] || '账号'
}

/** 加载科室（医生表单用） */
async function loadDepartments() {
  try {
    const res = await request.get('/departments/list')
    departments.value = res.data || []
  } catch {
    departments.value = []
  }
}

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
    list.value = parseListData(res).map((item, index) => ({
      ...item,
      seq: item.seq ?? (page.value - 1) * pageSize.value + index + 1,
    }))
    total.value = res.data?.total ?? list.value.length
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadList()
}

function handleReset() {
  keyword.value = ''
  page.value = 1
  loadList()
}

function handlePageChange() {
  loadList()
}

/** 角色标签样式（浅紫红主题） */
function roleTagType(role) {
  if (role === 'root' || role === 'admin') return 'danger'
  if (role === 'doctor') return 'warning'
  return 'primary'
}

function openCreate() {
  isEdit.value = false
  form.value = defaultForm()
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  form.value = {
    id: row.id,
    role: row.role,
    username: row.username,
    password: '',
    confirm_password: '',
    real_name: row.real_name || '',
    gender: row.gender ?? 1,
    age: row.age ?? null,
    phone: row.phone || '',
    email: row.email || '',
    allergy_history: row.allergy_history || '',
    department_id: row.department_id ?? null,
    title: row.title || '',
    specialty: row.specialty || '',
    introduction: row.introduction || '',
    status: row.status ?? 1,
  }
  dialogVisible.value = true
}

function validatePassword() {
  if (!isEdit.value) {
    if (!form.value.password) {
      ElMessage.warning('请输入密码')
      return false
    }
    if (form.value.password.length < 6) {
      ElMessage.warning('密码至少6个字符')
      return false
    }
    if (form.value.password !== form.value.confirm_password) {
      ElMessage.warning('两次密码输入不一致')
      return false
    }
  } else if (form.value.password) {
    if (form.value.password.length < 6) {
      ElMessage.warning('密码至少6个字符')
      return false
    }
    if (form.value.password !== form.value.confirm_password) {
      ElMessage.warning('两次密码输入不一致')
      return false
    }
  }
  return true
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
    if (form.value.role === 'doctor' && !form.value.real_name?.trim()) {
      ElMessage.warning('请输入医生姓名')
      return
    }
  }
  if (!validatePassword()) return

  submitting.value = true
  try {
    const role = form.value.role
    const prefix = apiPrefix(role)

    if (isEdit.value) {
      if (role === 'user') {
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
        await request.put(`${prefix}/${form.value.id}`, payload)
      } else if (role === 'doctor') {
        const payload = {
          real_name: form.value.real_name,
          department_id: form.value.department_id,
          title: form.value.title,
          specialty: form.value.specialty,
          introduction: form.value.introduction,
          phone: form.value.phone,
          status: form.value.status,
        }
        if (form.value.password) {
          payload.password = form.value.password
          payload.confirm_password = form.value.confirm_password
        }
        await request.put(`${prefix}/${form.value.id}`, payload)
      } else if (role === 'admin') {
        const payload = {
          nickname: form.value.real_name,
          phone: form.value.phone,
          email: form.value.email,
          status: form.value.status,
        }
        if (form.value.password) {
          payload.password = form.value.password
          payload.confirm_password = form.value.confirm_password
        }
        await request.put(`${prefix}/${form.value.id}`, payload)
      }
      ElMessage.success('更新成功')
    } else {
      if (role === 'user') {
        await request.post(`${prefix}/create`, {
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
      } else if (role === 'doctor') {
        await request.post(`${prefix}/create`, {
          username: form.value.username.trim(),
          password: form.value.password,
          confirm_password: form.value.confirm_password,
          real_name: form.value.real_name,
          department_id: form.value.department_id,
          title: form.value.title,
          specialty: form.value.specialty,
          introduction: form.value.introduction,
          phone: form.value.phone,
          status: form.value.status,
        })
      } else if (role === 'admin') {
        await request.post(`${prefix}/create`, {
          username: form.value.username.trim(),
          password: form.value.password,
          confirm_password: form.value.confirm_password,
          nickname: form.value.real_name,
          phone: form.value.phone,
          email: form.value.email,
          status: form.value.status,
        })
      }
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch { /* */ } finally {
    submitting.value = false
  }
}

/** 删除账号 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除${roleLabel(row.role)}「${row.username}」吗？`,
      '提示',
      { type: 'warning' },
    )
    await request.delete(`${apiPrefix(row.role)}/${row.id}`)
    ElMessage.success('删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    loadList()
  } catch { /* */ }
}

/** 切换账号状态 */
async function toggleStatus(row) {
  const newStatus = row.status === 1 ? 0 : 1
  const action = newStatus === 1 ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定${action}${roleLabel(row.role)}「${row.username}」吗？`, '提示', { type: 'warning' })
    await request.put(`${apiPrefix(row.role)}/${row.id}/status`, null, { params: { status: newStatus } })
    ElMessage.success(`${action}成功`)
    loadList()
  } catch { /* */ }
}

onMounted(() => {
  loadList()
  if (isRoot.value) loadDepartments()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="openCreate">
        {{ isRoot ? '新增账号' : '新增用户' }}
      </el-button>
    </div>

    <div class="modern-card">
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
        <el-table-column prop="seq" label="序号" min-width="70" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="real_name" label="昵称" min-width="100" />
        <el-table-column prop="gender" label="性别" min-width="70">
          <template #default="{ row }">
            <span v-if="row.gender">{{ row.gender === 2 ? '女' : '男' }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="age" label="年龄" min-width="70">
          <template #default="{ row }">{{ row.age ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="role_label" label="角色" min-width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small" effect="light">
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
            <template v-if="canManage(row)">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">
                {{ row.status === 1 ? '禁用' : '启用' }}
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
            <span v-else class="role-hint">超级管理员账号</span>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !list.length" description="暂无账号数据" />

      <AppPagination
        v-model:page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        @change="handlePageChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? `编辑${roleLabel(form.role)}` : (isRoot ? '新增账号' : '新增用户')"
      width="560px"
      destroy-on-close
    >
      <el-form label-width="90px">
        <el-form-item v-if="isRoot && !isEdit" label="角色" required>
          <el-radio-group v-model="form.role">
            <el-radio value="user">用户</el-radio>
            <el-radio value="doctor">医生</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
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
        <el-form-item :label="form.role === 'admin' ? '昵称' : form.role === 'doctor' ? '医生姓名' : '用户昵称'">
          <el-input v-model="form.real_name" :placeholder="form.role === 'doctor' ? '请输入医生姓名' : '请输入昵称'" />
        </el-form-item>

        <template v-if="form.role === 'user'">
          <el-form-item label="性别">
            <el-radio-group v-model="form.gender">
              <el-radio :value="1">男</el-radio>
              <el-radio :value="2">女</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="年龄">
            <el-input-number v-model="form.age" :min="1" :max="150" controls-position="right" />
          </el-form-item>
          <el-form-item label="过敏史">
            <el-input
              v-model="form.allergy_history"
              type="textarea"
              :rows="2"
              placeholder="请输入过敏史（选填）"
            />
          </el-form-item>
        </template>

        <template v-if="form.role === 'doctor'">
          <el-form-item label="所属科室">
            <el-select v-model="form.department_id" placeholder="请选择科室" clearable style="width: 100%">
              <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="职称">
            <el-input v-model="form.title" placeholder="如：主任医师" />
          </el-form-item>
          <el-form-item label="专长">
            <el-input v-model="form.specialty" placeholder="请输入专长" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="form.introduction" type="textarea" :rows="2" placeholder="医生简介（选填）" />
          </el-form-item>
        </template>

        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" maxlength="20" />
        </el-form-item>
        <el-form-item v-if="form.role === 'admin'" label="邮箱">
          <el-input v-model="form.email" placeholder="请输入邮箱（选填）" />
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
.role-hint {
  font-size: 12px;
  color: var(--text-secondary);
}
.text-muted {
  color: var(--text-secondary);
}
</style>
