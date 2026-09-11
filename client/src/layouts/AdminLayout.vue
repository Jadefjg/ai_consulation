<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { formatAvatar } from '@/utils/format'
import {
  DataAnalysis, User, FirstAidKit, OfficeBuilding, Collection,
  Share, ChatDotRound, Calendar, Document, Bell, Fold, ArrowDown,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)

/** 是否管理后台角色 */
function isAdminPanelRole(role) {
  return role === 'admin' || role === 'root'
}

/** 根据角色生成侧边栏菜单 */
const menuItems = computed(() => {
  if (isAdminPanelRole(userStore.role)) {
    return [
      { path: '/admin/dashboard', label: '数据概览', icon: DataAnalysis },
      { path: '/admin/users', label: '用户管理', icon: User },
      { path: '/admin/doctors', label: '医生管理', icon: FirstAidKit },
      { path: '/admin/departments', label: '科室管理', icon: OfficeBuilding },
      { path: '/admin/knowledge', label: '知识库', icon: Collection },
      { path: '/admin/graph', label: '知识图谱', icon: Share },
      { path: '/admin/consults', label: '咨询管理', icon: ChatDotRound },
      { path: '/admin/appointments', label: '预约管理', icon: Calendar },
      { path: '/admin/articles', label: '文章管理', icon: Document },
      { path: '/admin/notices', label: '公告管理', icon: Bell },
      { path: '/admin/schedules', label: '排班号源', icon: Calendar },
    ]
  }
  return [
    { path: '/doctor/dashboard', label: '工作台', icon: DataAnalysis },
    { path: '/doctor/consults', label: '待回复咨询', icon: ChatDotRound },
    { path: '/doctor/appointments', label: '我的预约', icon: Calendar },
    { path: '/doctor/patients', label: '患者档案', icon: User },
  ]
})

/** 面包屑路径 */
const breadcrumbs = computed(() => {
  const matched = route.matched.filter((r) => r.meta?.title)
  return matched.map((r) => ({ title: r.meta.title, path: r.path }))
})

/** 个人中心路径 */
const profilePath = computed(() =>
  isAdminPanelRole(userStore.role) ? '/admin/profile' : '/doctor/profile',
)

/** 头像地址 */
const avatarUrl = computed(() => formatAvatar(userStore.userInfo?.avatar))

/** 显示名称 */
const displayName = computed(() =>
  userStore.userInfo?.nickname || userStore.userInfo?.real_name || userStore.userInfo?.username || '用户',
)

/** 侧边栏标题 */
const sidebarTitle = computed(() =>
  isAdminPanelRole(userStore.role) ? '管理后台' : '医生工作台',
)

function goProfile() {
  router.push(profilePath.value)
}

function handleLogout() {
  userStore.logout()
}
</script>

<template>
  <el-container class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="sidebar-logo">
        <span v-if="!isCollapse" class="logo-text">{{ sidebarTitle }}</span>
        <span v-else class="logo-icon">🏥</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        router
        class="sidebar-menu"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="main-container">
      <!-- 顶部栏 -->
      <el-header class="top-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <!-- 右上角头像下拉 -->
        <el-dropdown trigger="click">
          <div class="header-user">
            <el-avatar :size="36" :src="avatarUrl">
              <el-icon><User /></el-icon>
            </el-avatar>
            <span class="username">{{ displayName }}</span>
            <el-icon><ArrowDown /></el-icon>
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
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
}

.sidebar {
  background: var(--sidebar-gradient);
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.logo-icon {
  font-size: 24px;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.78);
  font-weight: 500;
  margin: 4px 10px;
  border-radius: 8px;
  height: 44px;
  line-height: 44px;
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  color: rgba(255, 255, 255, 0.85);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.14) !important;
}

.sidebar-menu :deep(.el-menu-item:hover .el-icon) {
  color: #fff !important;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #fff !important;
  font-weight: 700;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.32) 0%,
    rgba(var(--color-brand-rgb), 0.55) 100%
  ) !important;
  box-shadow: inset 3px 0 0 #fff;
  border-right: none !important;
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: #fff !important;
}

.main-container {
  background: var(--bg-gradient);
}

.top-header {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.3s;
}

.collapse-btn:hover {
  color: var(--color-brand);
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.3s;
}

.header-user:hover {
  background: #f5f7fa;
}

.username {
  font-size: 14px;
  color: var(--text-primary);
}

.main-content {
  padding: 20px;
  min-height: calc(100vh - 60px);
}
</style>
