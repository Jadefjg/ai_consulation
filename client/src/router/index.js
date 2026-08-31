import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

/**
 * 路由配置
 */
const routes = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { public: true },
  },
  /* 用户门户路由 */
  {
    path: '/portal',
    component: () => import('@/layouts/PortalLayout.vue'),
    meta: { role: 'user' },
    children: [
      { path: '', redirect: '/portal/home' },
      { path: 'home', name: 'PortalHome', component: () => import('@/views/portal/Home.vue'), meta: { title: '首页' } },
      { path: 'chat', name: 'PortalChat', component: () => import('@/views/portal/Chat.vue'), meta: { title: 'AI问诊' } },
      { path: 'symptom', name: 'PortalSymptom', component: () => import('@/views/portal/Symptom.vue'), meta: { title: '症状推理' } },
      { path: 'consult', name: 'PortalConsult', component: () => import('@/views/portal/Consult.vue'), meta: { title: '在线咨询' } },
      { path: 'appointment', name: 'PortalAppointment', component: () => import('@/views/portal/Appointment.vue'), meta: { title: '预约挂号' } },
      { path: 'records', name: 'PortalRecords', component: () => import('@/views/portal/Records.vue'), meta: { title: '健康档案' } },
      { path: 'articles', name: 'PortalArticles', component: () => import('@/views/portal/Articles.vue'), meta: { title: '健康资讯' } },
      { path: 'articles/:id', name: 'PortalArticleDetail', component: () => import('@/views/portal/ArticleDetail.vue'), meta: { title: '资讯详情' } },
      { path: 'notices/:id', name: 'PortalNoticeDetail', component: () => import('@/views/portal/NoticeDetail.vue'), meta: { title: '公告详情' } },
      { path: 'profile', name: 'PortalProfile', component: () => import('@/views/portal/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },
  /* 医生路由 */
  {
    path: '/doctor',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { role: 'doctor' },
    children: [
      { path: '', redirect: '/doctor/dashboard' },
      { path: 'dashboard', name: 'DoctorDashboard', component: () => import('@/views/doctor/Dashboard.vue'), meta: { title: '工作台' } },
      { path: 'consults', name: 'DoctorConsults', component: () => import('@/views/doctor/Consults.vue'), meta: { title: '待回复咨询' } },
      { path: 'appointments', name: 'DoctorAppointments', component: () => import('@/views/doctor/Appointments.vue'), meta: { title: '我的预约' } },
      { path: 'patients', name: 'DoctorPatients', component: () => import('@/views/doctor/Patients.vue'), meta: { title: '患者档案' } },
      { path: 'profile', name: 'DoctorProfile', component: () => import('@/views/doctor/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },
  /* 管理员路由 */
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { role: 'admin' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { title: '数据概览' } },
      { path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/Users.vue'), meta: { title: '用户管理' } },
      { path: 'doctors', name: 'AdminDoctors', component: () => import('@/views/admin/Doctors.vue'), meta: { title: '医生管理' } },
      { path: 'departments', name: 'AdminDepartments', component: () => import('@/views/admin/Departments.vue'), meta: { title: '科室管理' } },
      { path: 'knowledge', name: 'AdminKnowledge', component: () => import('@/views/admin/Knowledge.vue'), meta: { title: '知识库' } },
      { path: 'graph', name: 'AdminGraph', component: () => import('@/views/admin/Graph.vue'), meta: { title: '知识图谱' } },
      { path: 'consults', name: 'AdminConsults', component: () => import('@/views/admin/Consults.vue'), meta: { title: '咨询管理' } },
      { path: 'appointments', name: 'AdminAppointments', component: () => import('@/views/admin/Appointments.vue'), meta: { title: '预约管理' } },
      { path: 'articles', name: 'AdminArticles', component: () => import('@/views/admin/Articles.vue'), meta: { title: '文章管理' } },
      { path: 'notices', name: 'AdminNotices', component: () => import('@/views/admin/Notices.vue'), meta: { title: '公告管理' } },
      { path: 'profile', name: 'AdminProfile', component: () => import('@/views/admin/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/** 角色对应的首页路径 */
const roleHomeMap = {
  user: '/portal/home',
  doctor: '/doctor/dashboard',
  admin: '/admin/dashboard',
  root: '/admin/dashboard',
}

/** 是否可访问管理后台路由 */
function canAccessAdminRoute(userRole, requiredRole) {
  if (userRole === requiredRole) return true
  if (requiredRole === 'admin' && userRole === 'root') return true
  return false
}

/**
 * 获取角色合法首页
 * @param {string} role - 用户角色
 * @returns {string|null} 首页路径，无效角色返回 null
 */
function getRoleHome(role) {
  return roleHomeMap[role] || null
}

/** 路由守卫：基于角色的访问控制 */
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 有 token 但角色无效时清理登录态，避免 /login 与业务页无限重定向
  if (userStore.isLoggedIn && !getRoleHome(userStore.role)) {
    userStore.clearAuth()
    if (to.meta.public) {
      next()
    } else {
      next('/login')
    }
    return
  }

  if (to.meta.public) {
    if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      next(getRoleHome(userStore.role))
    } else {
      next()
    }
    return
  }

  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }

  const requiredRole = to.matched.find((r) => r.meta.role)?.meta.role
  if (requiredRole && !canAccessAdminRoute(userStore.role, requiredRole)) {
    next(getRoleHome(userStore.role) || '/login')
    return
  }

  next()
})

export default router
