<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'
import { formatAvatar } from '@/utils/format'

const userStore = useUserStore()
const activeTab = ref('info')
const saving = ref(false)
const uploading = ref(false)

/** 当前用户角色 */
const userRole = computed(() => userStore.role)

/** 个人资料表单（按角色展示不同字段） */
const infoForm = reactive({
  nickname: '',
  real_name: '',
  phone: '',
  email: '',
  gender: 1,
  age: null,
  allergy_history: '',
  title: '',
  specialty: '',
  introduction: '',
})

/** 密码修改表单 */
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

/** 头像地址 */
const avatarUrl = computed(() => formatAvatar(userStore.userInfo?.avatar))

/** 显示名称（管理员用昵称，其他角色用姓名） */
const displayName = computed(() => {
  const info = userStore.userInfo
  if (userRole.value === 'admin') {
    return info?.nickname || info?.username || '用户'
  }
  return info?.real_name || info?.username || '用户'
})

/** 头像占位文字 */
const avatarText = computed(() => displayName.value?.[0] || 'U')

/**
 * 将后端性别数值转为前端展示
 * @param {number|null|undefined} val - 性别值 1男 2女
 */
function mapGenderFromApi(val) {
  if (val === 2) return 2
  return 1
}

/**
 * 加载用户资料并填充表单
 */
async function loadProfile() {
  try {
    const data = await userStore.fetchProfile()
    if (userRole.value === 'admin') {
      Object.assign(infoForm, {
        nickname: data.nickname || '',
        phone: data.phone || '',
        email: data.email || '',
      })
    } else if (userRole.value === 'doctor') {
      Object.assign(infoForm, {
        real_name: data.real_name || '',
        phone: data.phone || '',
        title: data.title || '',
        specialty: data.specialty || '',
        introduction: data.introduction || '',
      })
    } else {
      Object.assign(infoForm, {
        real_name: data.real_name || '',
        phone: data.phone || '',
        gender: mapGenderFromApi(data.gender),
        age: data.age ?? null,
        allergy_history: data.allergy_history || '',
      })
    }
  } catch { /* */ }
}

/**
 * 构建角色对应的提交数据（仅发送后端支持的字段）
 */
function buildSavePayload() {
  if (userRole.value === 'admin') {
    return {
      nickname: infoForm.nickname || null,
      phone: infoForm.phone || null,
      email: infoForm.email || null,
    }
  }
  if (userRole.value === 'doctor') {
    return {
      real_name: infoForm.real_name || null,
      phone: infoForm.phone || null,
      title: infoForm.title || null,
      specialty: infoForm.specialty || null,
      introduction: infoForm.introduction || null,
    }
  }
  return {
    real_name: infoForm.real_name || null,
    phone: infoForm.phone || null,
    gender: infoForm.gender ?? 1,
    age: infoForm.age ?? null,
    allergy_history: infoForm.allergy_history || null,
  }
}

/** 保存个人资料 */
async function saveInfo() {
  saving.value = true
  try {
    const payload = buildSavePayload()
    await request.put('/profile/update', payload)
    userStore.setUserInfo(payload)
    ElMessage.success('资料更新成功')
  } catch { /* */ } finally {
    saving.value = false
  }
}

/** 修改密码 */
async function changePassword() {
  if (pwdForm.new_password !== pwdForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  saving.value = true
  try {
    await request.put('/profile/password', pwdForm)
    ElMessage.success('密码修改成功')
    Object.assign(pwdForm, { old_password: '', new_password: '', confirm_password: '' })
  } catch { /* */ } finally {
    saving.value = false
  }
}

/** 上传头像 */
async function handleAvatarUpload({ file }) {
  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await request.post('/profile/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    userStore.setUserInfo({ avatar: res.data.avatar || res.data })
    ElMessage.success('头像上传成功')
  } catch { /* */ } finally {
    uploading.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="profile-panel">
    <el-row :gutter="24">
      <!-- 左侧菜单 -->
      <el-col :xs="24" :sm="6">
        <div class="profile-sidebar modern-card">
          <div class="avatar-section">
            <el-upload
              :show-file-list="false"
              :http-request="handleAvatarUpload"
              accept="image/*"
            >
              <el-avatar :size="80" :src="avatarUrl" class="avatar-click">
                {{ avatarText }}
              </el-avatar>
            </el-upload>
            <p class="avatar-tip">点击头像上传</p>
            <h3>{{ displayName }}</h3>
          </div>
          <el-menu :default-active="activeTab" @select="(k) => activeTab = k">
            <el-menu-item index="info">资料修改</el-menu-item>
            <el-menu-item index="password">密码修改</el-menu-item>
          </el-menu>
        </div>
      </el-col>

      <!-- 右侧内容 -->
      <el-col :xs="24" :sm="18">
        <div class="profile-content modern-card">
          <!-- 资料修改 -->
          <div v-show="activeTab === 'info'">
            <h3 class="content-title">个人资料</h3>
            <el-form :model="infoForm" label-width="90px" style="max-width:480px">
              <!-- 管理员：用户昵称、手机号、邮箱 -->
              <template v-if="userRole === 'admin'">
                <el-form-item label="用户昵称">
                  <el-input v-model="infoForm.nickname" placeholder="请输入用户昵称" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="infoForm.email" placeholder="请输入邮箱" />
                </el-form-item>
              </template>

              <!-- 医生：姓名、职称、专长等 -->
              <template v-else-if="userRole === 'doctor'">
                <el-form-item label="医生姓名">
                  <el-input v-model="infoForm.real_name" placeholder="请输入医生姓名" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item label="职称">
                  <el-input v-model="infoForm.title" placeholder="请输入职称" />
                </el-form-item>
                <el-form-item label="专长">
                  <el-input v-model="infoForm.specialty" placeholder="请输入专长领域" />
                </el-form-item>
                <el-form-item label="简介">
                  <el-input v-model="infoForm.introduction" type="textarea" :rows="3" placeholder="请输入个人简介" />
                </el-form-item>
              </template>

              <!-- 患者：姓名、性别、年龄等 -->
              <template v-else>
                <el-form-item label="用户昵称">
                  <el-input v-model="infoForm.real_name" placeholder="请输入用户昵称" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item label="性别">
                  <el-radio-group v-model="infoForm.gender">
                    <el-radio :value="1">男</el-radio>
                    <el-radio :value="2">女</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="年龄">
                  <el-input-number v-model="infoForm.age" :min="1" :max="150" />
                </el-form-item>
                <el-form-item label="过敏史">
                  <el-input v-model="infoForm.allergy_history" type="textarea" :rows="2" placeholder="请输入过敏史，无则填无" />
                </el-form-item>
              </template>

              <el-form-item>
                <el-button type="primary" class="gradient-btn" :loading="saving" @click="saveInfo">保存</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 密码修改 -->
          <div v-show="activeTab === 'password'">
            <h3 class="content-title">修改密码</h3>
            <el-form :model="pwdForm" label-width="100px" style="max-width:480px">
              <el-form-item label="原密码">
                <el-input v-model="pwdForm.old_password" type="password" show-password />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="pwdForm.new_password" type="password" show-password />
              </el-form-item>
              <el-form-item label="确认密码">
                <el-input v-model="pwdForm.confirm_password" type="password" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="gradient-btn" :loading="saving" @click="changePassword">修改密码</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.profile-sidebar {
  text-align: center;
  padding: 24px 16px;
}

.avatar-section {
  margin-bottom: 16px;
}

.avatar-click {
  cursor: pointer;
  border: 3px solid var(--color-brand);
}

.avatar-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 8px 0;
}

.profile-sidebar h3 {
  font-size: 16px;
}

.profile-sidebar .el-menu {
  border-right: none;
}

.content-title {
  font-size: 18px;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
</style>
