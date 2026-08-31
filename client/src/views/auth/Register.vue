<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { User, Lock, Phone, FirstAidKit } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const departments = ref([])

/** 角色选项（管理员仅后台创建） */
const roleOptions = [
  { label: '用户', value: 'user', icon: User },
  { label: '医生', value: 'doctor', icon: FirstAidKit },
]

/** 注册表单 */
const form = reactive({
  username: '',
  password: '',
  confirm_password: '',
  real_name: '',
  phone: '',
  role: 'user',
  department_id: null,
  title: '',
  specialty: '',
})

/** 加载科室列表 */
async function loadDepartments() {
  try {
    const res = await request.get('/departments/list')
    departments.value = res.data || []
  } catch {
    departments.value = []
  }
}

/** 提交注册 */
async function handleRegister() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  if (form.password !== form.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (form.role === 'doctor' && !form.department_id) {
    ElMessage.warning('请选择所属科室')
    return
  }
  loading.value = true
  try {
    await request.post('/auth/register', {
      username: form.username.trim(),
      password: form.password,
      confirm_password: form.confirm_password,
      real_name: form.real_name.trim() || undefined,
      phone: form.phone.trim() || undefined,
      role: form.role,
      department_id: form.role === 'doctor' ? form.department_id : undefined,
      title: form.role === 'doctor' ? form.title.trim() || undefined : undefined,
      specialty: form.role === 'doctor' ? form.specialty.trim() || undefined : undefined,
    })
    ElMessage.success('注册成功，请登录')
    router.push({ path: '/login', query: { role: form.role } })
  } catch {
    /* 错误已在拦截器处理 */
  } finally {
    loading.value = false
  }
}

onMounted(loadDepartments)
</script>

<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
    </div>
    <div class="auth-card">
      <div class="auth-header">
        <span class="auth-logo">🏥</span>
        <h1>账号注册</h1>
        <p>加入 AI 智能医疗问诊平台</p>
      </div>
      <el-form :model="form" size="large" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.real_name"
            :placeholder="form.role === 'doctor' ? '医生姓名' : '用户昵称'"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.phone" placeholder="手机号" :prefix-icon="Phone" />
        </el-form-item>
        <el-form-item>
          <label class="field-label">注册身份</label>
          <div class="role-cards">
            <button
              v-for="opt in roleOptions"
              :key="opt.value"
              type="button"
              class="role-card"
              :class="{ active: form.role === opt.value }"
              @click="form.role = opt.value"
            >
              <span class="role-icon-wrap">
                <el-icon :size="18"><component :is="opt.icon" /></el-icon>
              </span>
              <span class="role-label">{{ opt.label }}</span>
            </button>
          </div>
        </el-form-item>
        <template v-if="form.role === 'doctor'">
          <el-form-item>
            <el-select v-model="form.department_id" placeholder="选择所属科室" style="width:100%">
              <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.title" placeholder="职称（如：主治医师）" :prefix-icon="FirstAidKit" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.specialty" placeholder="擅长领域" :prefix-icon="FirstAidKit" />
          </el-form-item>
        </template>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.confirm_password" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="submit-btn" :loading="loading" native-type="submit">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="auth-footer">
        已有账号？
        <router-link to="/login" class="link">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  position: relative;
  overflow: hidden;
}

.auth-bg .bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.c1 { width: 350px; height: 350px; top: -80px; right: -80px; }
.c2 { width: 250px; height: 250px; bottom: -60px; left: -40px; }

.auth-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 1;
}

.auth-header {
  text-align: center;
  margin-bottom: 28px;
}

.auth-logo { font-size: 44px; }

.auth-header h1 {
  font-size: 22px;
  margin: 10px 0 6px;
  color: #11998e;
}

.auth-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.role-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.role-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 10px 4px;
  border-radius: 10px;
  border: 1.5px solid #e8eaef;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.25s ease;
  color: #606266;
  font-family: inherit;
}

.role-card:hover {
  border-color: rgba(17, 153, 142, 0.35);
  background: #fff;
}

.role-card.active {
  border-color: transparent;
  background: linear-gradient(135deg, #11998e, #38ef7d);
  color: #fff;
  box-shadow: 0 4px 16px rgba(17, 153, 142, 0.35);
}

.role-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: rgba(17, 153, 142, 0.08);
}

.role-card.active .role-icon-wrap {
  background: rgba(255, 255, 255, 0.2);
}

.role-label {
  font-size: 12px;
  font-weight: 500;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  background: linear-gradient(135deg, #11998e, #38ef7d) !important;
  border: none !important;
  border-radius: 12px !important;
}

.auth-footer {
  text-align: center;
  margin-top: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

.link {
  color: #11998e;
  font-weight: 500;
}
</style>
