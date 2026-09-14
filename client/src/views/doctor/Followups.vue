<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
const plans=ref([]), patients=ref([]), show=ref(false), form=ref({user_id:null,title:'',frequency_days:30,next_date:'',notes:''})
async function load(){plans.value=(await request.get('/p3/followups')).data||[]}
async function loadPatients(){patients.value=(await request.get('/records/doctor/patient-options')).data||[]}
async function submit(){if(!form.value.user_id||!form.value.title||!form.value.next_date)return ElMessage.warning('请填写患者、计划和日期');await request.post('/p3/followups',form.value);ElMessage.success('随访计划已创建');show.value=false;load()}
onMounted(()=>{load();loadPatients()})
</script>
<template><div><div class="page-header"><h2 class="page-title">随访管理</h2><el-button type="primary" @click="show=true">创建计划</el-button></div><div class="modern-card"><el-table :data="plans" stripe><el-table-column prop="user_id" label="患者ID"/><el-table-column prop="title" label="随访计划"/><el-table-column prop="next_date" label="下次随访"/><el-table-column prop="frequency_days" label="周期（天）"/><el-table-column label="状态"><template #default="{row}"><el-tag>{{row.status===1?'进行中':row.status===2?'已暂停':'已完成'}}</el-tag></template></el-table-column></el-table><el-empty v-if="!plans.length" description="暂无随访计划"/></div><el-dialog v-model="show" title="创建随访计划" width="520px"><el-form label-width="90px"><el-form-item label="患者" required><el-select v-model="form.user_id" style="width:100%"><el-option v-for="p in patients" :key="p.id" :label="p.name" :value="p.id"/></el-select></el-form-item><el-form-item label="计划名称" required><el-input v-model="form.title"/></el-form-item><el-form-item label="首次随访" required><el-date-picker v-model="form.next_date" value-format="YYYY-MM-DD" style="width:100%"/></el-form-item><el-form-item label="随访周期"><el-input-number v-model="form.frequency_days" :min="1" :max="365"/></el-form-item><el-form-item label="备注"><el-input v-model="form.notes" type="textarea"/></el-form-item></el-form><template #footer><el-button @click="show=false">取消</el-button><el-button type="primary" @click="submit">创建</el-button></template></el-dialog></div></template>
<style scoped>.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}.page-title{margin:0}</style>
