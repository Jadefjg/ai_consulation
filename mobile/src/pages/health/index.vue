<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  addChronicMetric,
  assessRisk,
  completeFollowup,
  createChronic,
  fetchChronicRecords,
  fetchFollowups,
} from '@/api/patient'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const followups = ref<any[]>([])
const chronicRecords = ref<any[]>([])
const risk = ref<any>(null)
const saving = ref(false)
const disease = ref('')
const metricForm = reactive({ chronicIndex: 0, metric: '', value: '' })
const completeText = ref('已按计划完成本次随访')
const riskForm = reactive({
  age: 0,
  chronic_count: 0,
  severe: false,
  emergency_symptom: false,
})

const planStatus: Record<number, string> = { 1: '进行中', 2: '已暂停', 3: '已完成' }
const chronicNames = computed(() => chronicRecords.value.map((item) => `${item.disease}（#${item.id}）`))

async function load() {
  if (!userStore.requireLogin()) return
  try {
    const [plans, records] = await Promise.all([fetchFollowups(), fetchChronicRecords()])
    followups.value = plans
    chronicRecords.value = records
    const info = userStore.userInfo || {}
    riskForm.age = Number(info.age || 0)
    riskForm.chronic_count = records.length
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

onShow(load)

function onChronicChange(event: any) {
  metricForm.chronicIndex = Number(event.detail.value)
}

async function handleComplete(item: any) {
  if (!item.task_id) {
    uni.showToast({ title: '当前没有待完成任务', icon: 'none' })
    return
  }
  uni.showModal({
    title: '完成随访',
    content: `确认完成「${item.title}」？下次将按 ${item.frequency_days || 30} 天滚动。`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await completeFollowup(item.task_id, completeText.value)
        uni.showToast({ title: '已完成', icon: 'success' })
        load()
      } catch (error: any) {
        uni.showToast({ title: error.message || '提交失败', icon: 'none' })
      }
    },
  })
}

async function handleCreateChronic() {
  if (!disease.value.trim()) {
    uni.showToast({ title: '请填写慢病名称，如高血压', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await createChronic(disease.value.trim())
    disease.value = ''
    uni.showToast({ title: '档案已创建', icon: 'success' })
    await load()
  } catch (error: any) {
    uni.showToast({ title: error.message || '创建失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function handleAddMetric() {
  const record = chronicRecords.value[metricForm.chronicIndex]
  if (!record || !metricForm.metric.trim() || !metricForm.value.trim()) {
    uni.showToast({ title: '请选择档案并填写指标、数值', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await addChronicMetric(record.id, metricForm.metric.trim(), metricForm.value.trim())
    metricForm.metric = ''
    metricForm.value = ''
    uni.showToast({ title: '指标已记录', icon: 'success' })
    await load()
  } catch (error: any) {
    uni.showToast({ title: error.message || '记录失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function handleAssess() {
  try {
    risk.value = await assessRisk({
      age: Number(riskForm.age) || 0,
      chronic_count: Number(riskForm.chronic_count) || chronicRecords.value.length,
      severe: riskForm.severe,
      emergency_symptom: riskForm.emergency_symptom,
    })
  } catch (error: any) {
    uni.showToast({ title: error.message || '评估失败', icon: 'none' })
  }
}
</script>

<template>
  <view class="page">
    <view class="hint">随访计划由医生在电脑端创建；您可在此完成任务、记录慢病指标并做风险评估。</view>

    <view class="card">
      <text class="title">随访计划</text>
      <view v-for="item in followups" :key="item.id" class="block">
        <text class="name">{{ item.title }}</text>
        <text class="meta">医生 {{ item.doctor_name || '-' }} · {{ planStatus[item.status] || item.status }}</text>
        <text class="meta">下次 {{ item.next_date }}{{ item.due_date ? ` · 待完成 ${item.due_date}` : '' }}</text>
        <button v-if="item.can_complete" size="mini" class="primary mini" @click="handleComplete(item)">完成此次随访</button>
      </view>
      <view v-if="!followups.length" class="empty">暂无随访，待医生创建计划后会出现在这里</view>
    </view>

    <view class="card">
      <text class="title">慢病档案</text>
      <input v-model="disease" class="input" placeholder="慢病名称，如高血压、糖尿病" />
      <button class="primary" :loading="saving" @click="handleCreateChronic">新建档案</button>
      <picker :range="chronicNames" :disabled="!chronicNames.length" @change="onChronicChange">
        <view class="picker">{{ chronicNames[metricForm.chronicIndex] || '请选择要记录的档案' }}</view>
      </picker>
      <input v-model="metricForm.metric" class="input" placeholder="指标，如血压、血糖" />
      <input v-model="metricForm.value" class="input" placeholder="数值，如 128/82" />
      <button class="primary" :loading="saving" @click="handleAddMetric">记录指标</button>
      <view v-for="item in chronicRecords" :key="item.id" class="block">
        <text class="name">{{ item.disease }}</text>
        <text v-for="metric in item.recent_metrics || []" :key="metric.id" class="meta">
          {{ metric.metric }} {{ metric.value }} · {{ metric.measured_at }}
        </text>
        <text v-if="!(item.recent_metrics || []).length" class="meta">暂无指标</text>
      </view>
    </view>

    <view class="card">
      <text class="title">风险评估</text>
      <view class="row">
        <text class="label">年龄</text>
        <input v-model="riskForm.age" class="input grow" type="number" />
      </view>
      <view class="row">
        <text class="label">慢病数</text>
        <input v-model="riskForm.chronic_count" class="input grow" type="number" />
      </view>
      <view class="checks">
        <text class="check" :class="{ on: riskForm.severe }" @click="riskForm.severe = !riskForm.severe">症状严重</text>
        <text class="check" :class="{ on: riskForm.emergency_symptom }" @click="riskForm.emergency_symptom = !riskForm.emergency_symptom">疑似急症</text>
      </view>
      <button class="primary" @click="handleAssess">开始评估</button>
      <view v-if="risk" class="risk" :class="risk.level">
        <text class="name">{{ risk.level }} · {{ risk.score }} 分</text>
        <text class="meta">{{ risk.advice }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx 24rpx 48rpx; }
.hint { background: #fff4e5; color: #8a5a00; border-radius: 16rpx; padding: 20rpx; margin-bottom: 20rpx; font-size: 24rpx; }
.card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; }
.title { display: block; font-weight: 700; margin-bottom: 16rpx; }
.block { padding: 16rpx 0; border-top: 1rpx solid #f0f1f5; }
.name { display: block; font-weight: 600; }
.meta { display: block; color: #8a8f99; margin-top: 8rpx; }
.input, .picker { background: #f5f6fa; border-radius: 12rpx; padding: 20rpx; margin: 12rpx 0; }
.primary { background: #b56bc4; color: #fff; margin-top: 8rpx; }
.mini { display: inline-block; margin-top: 16rpx; }
.row { display: flex; align-items: center; gap: 16rpx; }
.label { width: 120rpx; color: #666; }
.grow { flex: 1; }
.checks { display: flex; gap: 16rpx; margin: 12rpx 0 20rpx; }
.check { padding: 12rpx 20rpx; border-radius: 999rpx; background: #f5f6fa; color: #666; }
.check.on { background: #f3e6f7; color: #b56bc4; }
.risk { margin-top: 20rpx; padding: 20rpx; border-radius: 12rpx; background: #f7eef9; }
.risk.高风险 { background: #fdeaea; }
.empty { color: #8a8f99; padding: 12rpx 0; }
</style>
