<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { User, Lock, Setting, ChatDotRound, Calendar, FirstAidKit, DataAnalysis } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)

/** 登录表单 */
const form = reactive({
  username: '',
  password: '',
  role: 'user',
})

onMounted(() => {
  const queryRole = route.query.role
  if (queryRole && ['user', 'doctor', 'admin'].includes(queryRole)) {
    form.role = queryRole
  }
})

/** 角色选项 */
const roleOptions = [
  { label: '用户', value: 'user', icon: User },
  { label: '医生', value: 'doctor', icon: FirstAidKit },
  { label: '管理员', value: 'admin', icon: Setting },
]

/** 平台特色介绍 */
const features = [
  { icon: ChatDotRound, title: 'AI 智能问诊', desc: '基于大模型的症状分析与健康咨询' },
  { icon: Calendar, title: '在线预约挂号', desc: '科室医生一键预约，省时省心' },
  { icon: FirstAidKit, title: '专业医疗服务', desc: '连接优质医生资源，守护您的健康' },
  { icon: DataAnalysis, title: '健康数据管理', desc: '问诊记录与档案一站式管理' },
]

/** 提交登录 */
async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    const homeMap = { user: '/portal/home', doctor: '/doctor/dashboard', admin: '/admin/dashboard', root: '/admin/dashboard' }
    router.push(homeMap[form.role] || homeMap[userStore.role] || '/portal/home')
  } catch {
    /* 错误已在拦截器处理 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 左侧：全屏背景图 + 品牌介绍 -->
    <div class="login-left">
      <div class="left-bg"></div>
      <div class="left-overlay"></div>
      <div class="left-deco">
        <div class="deco-circle c1"></div>
        <div class="deco-circle c2"></div>
        <div class="deco-circle c3"></div>
      </div>
      <div class="left-content">
        <div class="brand">
          <div class="brand-badge">
            <span class="brand-logo">🏥</span>
            <span class="brand-tag">智慧医疗</span>
          </div>
          <h1>AI 智能医疗问诊平台</h1>
          <p class="brand-slogan">专业 · 智能 · 便捷的健康服务</p>
        </div>
        <p class="brand-desc">
          融合人工智能与专业医疗知识，为您提供 7×24 小时在线健康咨询、
          智能症状分析、预约挂号及健康档案管理等一站式医疗服务。
        </p>
        <ul class="feature-list">
          <li v-for="item in features" :key="item.title" class="feature-item">
            <div class="feature-icon">
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
            </div>
            <div class="feature-text">
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- 右侧：登录表单（自适应 1/3 宽度） -->
    <div class="login-right">
      <div class="right-bg-pattern">
        <div class="pattern-dot d1"></div>
        <div class="pattern-dot d2"></div>
      </div>
      <div class="right-inner">
        <div class="form-brand">
          <div class="form-brand-badge">
            <span class="form-brand-icon">🏥</span>
          </div>
          <div class="form-brand-info">
            <span class="form-brand-text">账号登录</span>
            <span class="form-brand-sub">AI 智能医疗问诊平台</span>
          </div>
        </div>

        <div class="form-panel">
          <div class="form-panel-accent"></div>
          <div class="form-header">
            <h2>欢迎回来</h2>
            <p>登录后即可使用 AI 问诊与健康服务</p>
          </div>

          <el-form :model="form" size="large" class="login-form" @submit.prevent="handleLogin">
            <div class="field-group">
              <label class="field-label">用户名</label>
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                class="custom-input"
              />
            </div>
            <div class="field-group">
              <label class="field-label">密码</label>
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                class="custom-input"
              />
            </div>
            <div class="field-group">
              <label class="field-label">登录身份</label>
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
            </div>
            <el-button type="primary" class="submit-btn" :loading="loading" native-type="submit">
              {{ loading ? '登录中...' : '立即登录' }}
            </el-button>
          </el-form>

          <div class="form-footer">
            <span>还没有账号？</span>
            <router-link to="/register" class="link">免费注册 →</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  overflow: hidden;
}

/* ===== 左侧面板：全屏背景图 ===== */
.login-left {
  flex: 2;
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.left-bg {
  position: absolute;
  inset: 0;
  background: url('/login-bg.png') center center / cover no-repeat;
  transform: scale(1.02);
}

.left-overlay {
  position: absolute;
  inset: 0;
  background: var(--overlay-auth);
}

.left-deco .deco-circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
}

.deco-circle.c1 {
  width: 280px;
  height: 280px;
  top: -80px;
  right: -60px;
}

.deco-circle.c2 {
  width: 160px;
  height: 160px;
  bottom: 60px;
  left: -40px;
}

.deco-circle.c3 {
  width: 100px;
  height: 100px;
  bottom: 30%;
  right: 15%;
}

.left-content {
  position: relative;
  z-index: 2;
  max-width: 540px;
  padding: 56px 48px;
  color: #fff;
}

.brand {
  margin-bottom: 24px;
}

.brand-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.brand-logo {
  font-size: 44px;
  line-height: 1;
}

.brand-tag {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  letter-spacing: 2px;
}

.brand h1 {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.35;
  margin: 0 0 12px;
  letter-spacing: 1px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.brand-slogan {
  font-size: 16px;
  opacity: 0.92;
  margin: 0;
  letter-spacing: 3px;
}

.brand-desc {
  font-size: 15px;
  line-height: 1.85;
  opacity: 0.88;
  margin: 0 0 40px;
  padding-left: 14px;
  border-left: 3px solid rgba(255, 255, 255, 0.4);
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: background 0.3s;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.16);
}

.feature-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.feature-text strong {
  font-size: 14px;
  font-weight: 600;
}

.feature-text span {
  font-size: 12px;
  opacity: 0.78;
  line-height: 1.45;
}

/* ===== 右侧面板：自适应宽度表单 ===== */
.login-right {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f7f9fc;
  padding: clamp(24px, 4vw, 48px) clamp(20px, 3.5vw, 40px);
  overflow: hidden;
}

.right-bg-pattern {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 85% 8%, rgba(var(--color-brand-rgb), 0.14) 0%, transparent 42%),
    radial-gradient(circle at 8% 92%, rgba(var(--color-brand-dark-rgb), 0.1) 0%, transparent 38%),
    linear-gradient(180deg, #fdf4ff 0%, #ffffff 100%);
  pointer-events: none;
}

.right-bg-pattern::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, var(--color-brand) 0%, var(--color-brand-dark) 50%, rgba(var(--color-brand-dark-rgb), 0.3) 100%);
}

.pattern-dot {
  position: absolute;
  border-radius: 50%;
  background: rgba(var(--color-brand-rgb), 0.06);
  pointer-events: none;
}

.pattern-dot.d1 {
  width: clamp(120px, 18vw, 200px);
  height: clamp(120px, 18vw, 200px);
  top: 8%;
  right: -8%;
}

.pattern-dot.d2 {
  width: clamp(80px, 12vw, 140px);
  height: clamp(80px, 12vw, 140px);
  bottom: 12%;
  left: -5%;
}

.right-inner {
  position: relative;
  z-index: 1;
  width: clamp(280px, 88%, 440px);
  display: flex;
  flex-direction: column;
  gap: clamp(16px, 2.5vw, 24px);
}

.form-brand {
  display: flex;
  align-items: center;
  gap: clamp(10px, 1.5vw, 14px);
  padding: 0 4px;
}

.form-brand-badge {
  width: clamp(40px, 5vw, 48px);
  height: clamp(40px, 5vw, 48px);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(var(--color-brand-rgb), 0.12), rgba(var(--color-brand-dark-rgb), 0.12));
  border: 1px solid rgba(var(--color-brand-rgb), 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.form-brand-icon {
  font-size: clamp(22px, 3vw, 26px);
  line-height: 1;
}

.form-brand-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.form-brand-text {
  font-size: clamp(14px, 1.6vw, 16px);
  font-weight: 700;
  color: var(--color-brand);
  letter-spacing: 0.5px;
}

.form-brand-sub {
  font-size: clamp(11px, 1.2vw, 12px);
  color: #a0a8b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.form-panel {
  position: relative;
  background: #fff;
  border-radius: clamp(16px, 2vw, 22px);
  padding: clamp(24px, 3.5vw, 32px) clamp(20px, 3vw, 28px) clamp(20px, 2.5vw, 26px);
  box-shadow:
    0 1px 3px rgba(var(--color-brand-rgb), 0.04),
    0 8px 32px rgba(var(--color-brand-rgb), 0.08),
    0 16px 48px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(var(--color-brand-rgb), 0.08);
  overflow: hidden;
}

.form-panel-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-brand), var(--color-brand-dark), var(--color-brand));
  background-size: 200% 100%;
  animation: accent-flow 4s ease infinite;
}

@keyframes accent-flow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.form-header {
  margin-bottom: clamp(20px, 2.5vw, 28px);
  padding-bottom: clamp(16px, 2vw, 20px);
  border-bottom: 1px solid #f0f2f7;
}

.form-header h2 {
  font-size: clamp(20px, 2.2vw, 24px);
  font-weight: 700;
  margin: 0 0 8px;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--color-brand) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.form-header p {
  font-size: clamp(12px, 1.3vw, 13px);
  color: #909399;
  margin: 0;
  line-height: 1.6;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: clamp(14px, 1.8vw, 18px);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: clamp(5px, 0.8vw, 8px);
}

.field-label {
  font-size: clamp(12px, 1.2vw, 13px);
  font-weight: 600;
  color: #606266;
  padding-left: 2px;
}

.login-form :deep(.custom-input) {
  width: 100%;
}

.login-form :deep(.custom-input .el-input__wrapper) {
  border-radius: clamp(10px, 1.2vw, 12px);
  padding: clamp(2px, 0.5vw, 4px) clamp(10px, 1.5vw, 14px);
  box-shadow: 0 0 0 1px #e8eaef inset;
  transition: box-shadow 0.25s, background 0.25s, transform 0.2s;
  background: #f9fafb;
}

.login-form :deep(.custom-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c8cdd8 inset;
  background: #fff;
}

.login-form :deep(.custom-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(var(--color-brand-rgb), 0.28) inset !important;
  background: #fff;
  transform: translateY(-1px);
}

.login-form :deep(.custom-input .el-input__inner) {
  height: clamp(38px, 4.5vw, 44px);
  font-size: clamp(13px, 1.4vw, 14px);
}

.login-form :deep(.custom-input .el-input__prefix) {
  color: #909399;
}

.role-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: clamp(6px, 1vw, 10px);
}

.role-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: clamp(4px, 0.6vw, 6px);
  padding: clamp(8px, 1.2vw, 12px) clamp(4px, 0.8vw, 6px);
  border-radius: clamp(10px, 1.2vw, 12px);
  border: 1.5px solid #e8eaef;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.25s ease;
  color: #606266;
  font-family: inherit;
  min-width: 0;
}

.role-card:hover {
  border-color: rgba(var(--color-brand-rgb), 0.35);
  background: #fff;
  transform: translateY(-1px);
}

.role-card.active {
  border-color: transparent;
  background: linear-gradient(135deg, var(--color-brand), var(--color-brand-dark));
  color: #fff;
  box-shadow: 0 4px 16px rgba(var(--color-brand-rgb), 0.35);
  transform: translateY(-2px);
}

.role-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: clamp(28px, 3.5vw, 32px);
  height: clamp(28px, 3.5vw, 32px);
  border-radius: 8px;
  background: rgba(var(--color-brand-rgb), 0.08);
  transition: background 0.25s;
}

.role-card.active .role-icon-wrap {
  background: rgba(255, 255, 255, 0.2);
}

.role-label {
  font-size: clamp(11px, 1.2vw, 12px);
  font-weight: 500;
  white-space: nowrap;
}

.submit-btn {
  width: 100%;
  height: clamp(42px, 4.8vw, 46px);
  margin-top: clamp(4px, 0.8vw, 8px);
  font-size: clamp(14px, 1.5vw, 15px);
  font-weight: 600;
  letter-spacing: clamp(1px, 0.3vw, 3px);
  background: linear-gradient(135deg, var(--color-brand) 0%, var(--color-brand-dark) 100%) !important;
  border: none !important;
  border-radius: clamp(10px, 1.2vw, 12px) !important;
  box-shadow: 0 4px 16px rgba(var(--color-brand-rgb), 0.32);
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(var(--color-brand-rgb), 0.42);
}

.submit-btn:active {
  transform: translateY(0);
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: clamp(18px, 2.2vw, 24px);
  padding-top: clamp(14px, 1.8vw, 18px);
  border-top: 1px dashed #e8eaef;
  font-size: clamp(12px, 1.3vw, 13px);
  color: #909399;
}

.link {
  color: var(--color-brand);
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s, transform 0.2s;
}

.link:hover {
  color: var(--color-brand-dark);
  transform: translateX(2px);
}

.form-trust {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(10px, 1.5vw, 14px);
  padding: 0 4px;
}

.trust-item {
  font-size: clamp(10px, 1.1vw, 11px);
  color: #b0b8c9;
  letter-spacing: 0.3px;
}

.trust-divider {
  width: 1px;
  height: 12px;
  background: #dce0e8;
}

/* ===== 响应式适配 ===== */
@media (max-width: 960px) {
  .login-page {
    flex-direction: column;
  }

  .login-left {
    min-height: 360px;
    flex: none;
  }

  .left-content {
    padding: 36px 24px;
    max-width: 100%;
  }

  .brand h1 {
    font-size: 24px;
  }

  .feature-list {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .feature-item {
    padding: 10px 14px;
  }

  .login-right {
    width: 100%;
    min-width: unset;
    flex: 1;
    min-height: auto;
    padding: 28px 20px 36px;
  }

  .right-inner {
    width: min(92%, 480px);
  }
}
</style>
