<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  cancelAppointment,
  createAppointment,
  fetchAvailableSchedules,
  fetchDepartments,
  fetchDoctors,
  fetchMyAppointments,
} from '@/api/patient'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const list = ref<any[]>([])
const departments = ref<any[]>([])
const doctors = ref<any[]>([])
const schedules = ref<any[]>([])
const creating = ref(false)
const form = reactive({
  departmentIndex: -1,
  doctorIndex: -1,
  scheduleIndex: -1,
  remark: '',
})

const statusMap: Record<number, string> = { 0: '待确认', 1: '已确认', 2: '已完成', 3: '已取消', 4: '爽约' }
const deptNames = computed(() => departments.value.map((item) => item.name))
const doctorNames = computed(() => doctors.value.map((item) => `${item.real_name}${item.title ? ' · ' + item.title : ''}`))
const scheduleNames = computed(() => schedules.value.map((item) => {
  const mark = item.bookable ? `余${item.remaining}` : '不可约'
  return `${item.date} ${item.time_slot}（${mark}）`
}))

async function loadList() {
  if (!userStore.requireLogin()) return
  try {
    list.value = await fetchMyAppointments()
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

onShow(async () => {
  if (!userStore.requireLogin()) return
  await loadList()
  try {
    departments.value = await fetchDepartments()
  } catch {
    departments.value = []
  }
})

async function onDeptChange(event: any) {
  form.departmentIndex = Number(event.detail.value)
  form.doctorIndex = -1
  form.scheduleIndex = -1
  doctors.value = []
  schedules.value = []
  const dept = departments.value[form.departmentIndex]
  if (!dept) return
  try {
    doctors.value = await fetchDoctors(dept.id)
  } catch (error: any) {
    doctors.value = []
    uni.showToast({ title: error.message || '医生加载失败', icon: 'none' })
  }
}

async function onDoctorChange(event: any) {
  form.doctorIndex = Number(event.detail.value)
  form.scheduleIndex = -1
  schedules.value = []
  const doctor = doctors.value[form.doctorIndex]
  if (!doctor) return
  try {
    schedules.value = await fetchAvailableSchedules(doctor.id)
  } catch (error: any) {
    schedules.value = []
    uni.showToast({ title: error.message || '号源加载失败', icon: 'none' })
  }
}

function onScheduleChange(event: any) {
  form.scheduleIndex = Number(event.detail.value)
}

async function submit() {
  if (creating.value) return
  const dept = departments.value[form.departmentIndex]
  const doctor = doctors.value[form.doctorIndex]
  const schedule = schedules.value[form.scheduleIndex]
  if (!dept || !doctor || !schedule) {
    uni.showToast({ title: '请选择科室、医生和号源', icon: 'none' })
    return
  }
  if (!schedule.bookable) {
    uni.showToast({ title: schedule.unavailable_reason || '该时段不可预约', icon: 'none' })
    return
  }
  creating.value = true
  try {
    await createAppointment({
      department_id: dept.id,
      doctor_id: doctor.id,
      visit_date: schedule.date,
      time_slot: schedule.time_slot,
      remark: form.remark,
    })
    uni.showToast({ title: '预约成功', icon: 'success' })
    form.remark = ''
    form.scheduleIndex = -1
    await loadList()
    schedules.value = await fetchAvailableSchedules(doctor.id)
  } catch (error: any) {
    uni.showToast({ title: error.message || '预约失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}

function handleCancel(item: any) {
  uni.showModal({
    title: '取消预约',
    content: `确认取消 ${item.visit_date} ${item.time_slot} 的预约？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await cancelAppointment(item.id)
        uni.showToast({ title: '已取消', icon: 'success' })
        loadList()
      } catch (error: any) {
        uni.showToast({ title: error.message || '取消失败', icon: 'none' })
      }
    },
  })
}
</script>

<template>
  <view class="page">
    <view class="card">
      <text class="title">新建预约</text>
      <picker :range="deptNames" @change="onDeptChange">
        <view class="picker">{{ deptNames[form.departmentIndex] || '选择科室' }}</view>
      </picker>
      <picker :range="doctorNames" :disabled="!doctorNames.length" @change="onDoctorChange">
        <view class="picker">{{ doctorNames[form.doctorIndex] || '选择医生' }}</view>
      </picker>
      <picker :range="scheduleNames" :disabled="!scheduleNames.length" @change="onScheduleChange">
        <view class="picker">{{ scheduleNames[form.scheduleIndex] || (scheduleNames.length ? '选择号源' : '暂无号源') }}</view>
      </picker>
      <input v-model="form.remark" class="input" placeholder="备注（选填）" />
      <button class="primary" :loading="creating" @click="submit">提交预约</button>
    </view>

    <view v-for="item in list" :key="item.id" class="card">
      <text class="name">{{ item.department_name }} · {{ item.doctor_name }}</text>
      <text class="meta">{{ item.visit_date }} {{ item.time_slot }}</text>
      <text class="meta">状态 {{ statusMap[item.status] || item.status }}</text>
      <button v-if="item.status === 0 || item.status === 1" size="mini" class="ghost" @click="handleCancel(item)">取消预约</button>
    </view>
    <view v-if="!list.length" class="empty">暂无预约</view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; }
.title, .name { display: block; font-weight: 700; margin-bottom: 16rpx; }
.picker, .input { background: #f5f6fa; border-radius: 12rpx; padding: 20rpx; margin-bottom: 16rpx; }
.primary { background: #b56bc4; color: #fff; }
.meta { display: block; color: #666; margin-top: 8rpx; }
.ghost { margin-top: 16rpx; }
.empty { text-align: center; color: #8a8f99; padding: 40rpx 0; }
</style>
