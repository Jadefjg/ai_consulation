<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { parseListData } from '@/utils/format'
const doctors = ref([]); const form = ref({ doctor_id: '', work_date: '', time_slot: '上午', capacity: 1 })
async function load() { const r = await request.get('/doctors/list', { params: { page_size: 100 } }); doctors.value = parseListData(r) }
async function submit() { if (!form.value.doctor_id || !form.value.work_date) return ElMessage.warning('请选择医生和日期'); await request.post('/appointments/admin/schedules', null, { params: form.value }); ElMessage.success('排班创建成功') }
onMounted(load)
</script>
<template><div><h2 class="page-title">医生排班与号源</h2><div class="modern-card"><el-form inline><el-form-item label="医生"><el-select v-model="form.doctor_id"><el-option v-for="d in doctors" :key="d.id" :value="d.id" :label="d.real_name" /></el-select></el-form-item><el-form-item label="日期"><el-date-picker v-model="form.work_date" value-format="YYYY-MM-DD" type="date" /></el-form-item><el-form-item label="时段"><el-select v-model="form.time_slot"><el-option v-for="s in ['上午','下午','晚上']" :key="s" :value="s" :label="s" /></el-select></el-form-item><el-form-item label="号源"><el-input-number v-model="form.capacity" :min="1" :max="100" /></el-form-item><el-button type="primary" @click="submit">创建排班</el-button></el-form></div></div></template>
