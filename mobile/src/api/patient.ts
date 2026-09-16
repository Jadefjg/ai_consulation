import { asList, request } from '@/api/request'

export function loginByPassword(username: string, password: string) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data: { username, password, role: 'user' },
  })
}

export function loginByWechat(code: string, nickname?: string) {
  return request({
    url: '/auth/wechat',
    method: 'POST',
    data: { code, nickname },
  })
}

export function fetchProfile() {
  return request({ url: '/profile/info' })
}

export function updateProfile(payload: Record<string, unknown>) {
  return request({ url: '/profile/update', method: 'PUT', data: payload })
}

export function fetchUserOverview() {
  return request({ url: '/stat/user-overview' })
}

export function fetchNotices() {
  return request({ url: '/notices/list' }).then(asList)
}

export function fetchNotice(id: number) {
  return request({ url: `/notices/${id}` })
}

export function fetchArticles(page = 1, pageSize = 10) {
  return request({ url: `/articles/list?page=${page}&page_size=${pageSize}` })
}

export function fetchArticle(id: number) {
  return request({ url: `/articles/${id}` })
}

export function fetchChatSessions() {
  return request({ url: '/chat/sessions' }).then(asList)
}

export function fetchChatMessages(sessionId: number) {
  return request({ url: `/chat/sessions/${sessionId}/messages` }).then(asList)
}

export function sendChat(message: string, sessionId?: number | null) {
  return request({
    url: '/chat/send?stream=0',
    method: 'POST',
    data: sessionId ? { session_id: sessionId, message } : { message },
    timeout: 120000,
  })
}

export function transferToDoctor(sessionId: number) {
  return request({
    url: '/clinical/transfer',
    method: 'POST',
    data: { session_id: sessionId },
  })
}

export function fetchDepartments() {
  return request({ url: '/departments/list' }).then(asList)
}

export function fetchDoctors(departmentId?: number) {
  const query = departmentId
    ? `/doctors/list?page_size=100&department_id=${departmentId}`
    : '/doctors/list?page_size=100'
  return request({ url: query }).then(asList)
}

export function fetchMyAppointments() {
  return request({ url: '/appointments/my' }).then(asList)
}

export function fetchAvailableSchedules(doctorId: number) {
  return request({ url: `/appointments/available-schedules?doctor_id=${doctorId}` }).then(asList)
}

export function createAppointment(payload: Record<string, unknown>) {
  return request({ url: '/appointments/create', method: 'POST', data: payload })
}

export function cancelAppointment(id: number) {
  return request({ url: `/appointments/my/${id}/cancel`, method: 'PUT' })
}

export function fetchMyConsults() {
  return request({ url: '/consult/my' }).then(asList)
}

export function createConsult(payload: Record<string, unknown>) {
  return request({ url: '/consult/create', method: 'POST', data: payload })
}

export function fetchMyRecords() {
  return request({ url: '/records/my' }).then(asList)
}

export function fetchFollowups() {
  return request({ url: '/p3/followups' }).then(asList)
}

export function completeFollowup(taskId: number, response: string) {
  return request({
    url: `/p3/followups/${taskId}/complete`,
    method: 'POST',
    data: { response },
  })
}

export function fetchChronicRecords() {
  return request({ url: '/p3/chronic' }).then(asList)
}

export function createChronic(disease: string) {
  return request({ url: '/p3/chronic', method: 'POST', data: { disease } })
}

export function addChronicMetric(chronicId: number, metric: string, value: string) {
  return request({
    url: `/p3/chronic/${chronicId}/metrics`,
    method: 'POST',
    data: { metric, value },
  })
}

export function assessRisk(factors: Record<string, unknown>) {
  return request({ url: '/p3/risk/assess', method: 'POST', data: { factors } })
}
