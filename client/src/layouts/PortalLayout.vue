<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { formatAvatar } from '@/utils/format'
import {
  HomeFilled, ChatDotRound, FirstAidKit, Document,
  Calendar, Notebook, Reading, User,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

/** 顶部导航菜单 */
const navItems = [
  { path: '/portal/home', label: '首页', icon: HomeFilled },
  { path: '/portal/chat', label: 'AI问诊', icon: ChatDotRound },
  { path: '/portal/symptom', label: '症状推理', icon: FirstAidKit },
  { path: '/portal/consult', label: '在线咨询', icon: Document },
  { path: '/portal/appointment', label: '预约挂号', icon: Calendar },
  { path: '/portal/records', label: '健康档案', icon: Notebook },
  { path: '/portal/articles', label: '健康资讯', icon: Reading },
]

/** 当前激活路径 */
const activePath = computed(() => route.path)

/** 头像地址 */
const avatarUrl = computed(() => formatAvatar(userStore.userInfo?.avatar))

/** 跳转个人中心 */
function goProfile() {
  router.push('/portal/profile')
}

/** 退出登录 */
function handleLogout() {
  userStore.logout()
}
</script>

<template>
  <div class="portal-layout">
    <!-- 渐变顶部导航 -->
    <header class="portal-header">
      <div class="header-inner">
        <div class="logo" @click="router.push('/portal/home')">
          <span class="logo-icon">🏥</span>
          <span class="logo-text">AI智能医疗问诊平台</span>
        </div>
        <nav class="nav-menu">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: activePath.startsWith(item.path) }"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
        <div class="header-user">
          <el-dropdown trigger="click">
            <div class="user-info">
              <el-avatar :size="36" :src="avatarUrl">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.real_name || userStore.userInfo?.username || '用户' }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goProfile">
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  安全退出
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>
    <!-- 主内容区 -->
    <main class="portal-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.portal-layout {
  min-height: 100vh;
  background: var(--bg-gradient);
}

.portal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  overflow-x: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 20px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  transition: all 0.3s;
  white-space: nowrap;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.header-user {
  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  color: #fff;
  font-size: 14px;
}

.portal-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  min-height: calc(100vh - 64px);
}
</style>
