<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'
import AppPagination from '@/components/AppPagination.vue'

const list = ref([])
const departments = ref([])
const loading = ref(false)
const keyword = ref('')
const departmentFilter = ref('')
const visitDateFilter = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

/** 预约状态映射 */
const statusMap = {
  0: '待确认',
  1: '已确认',
  2: '已完成',
  3: '已取消',
}

/** 加载科室列表（用于下拉选择） */
async function loadDepartments() {
  try {
    const res = await request.get('/departments/list')
    departments.value = res.data || []
  } catch {
    departments.value = []
  }
}

/** 加载预约列表（管理端） */
async function loadList() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim(),
    }
    if (departmentFilter.value !== '') {
      params.department_id = departmentFilter.value
    }
    if (visitDateFilter.value) {
      params.visit_date = visitDateFilter.value
    }
    if (statusFilter.value !== '') {
      params.status = statusFilter.value
    }
    const res = await request.get('/appointments/admin/list', { params })
    list.value = parseListData(res)
    total.value = res.data?.total ?? list.value.length
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** 搜索预约 */
function handleSearch() {
  page.value = 1
  loadList()
}

/** 重置搜索条件 */
function handleReset() {
  keyword.value = ''
  departmentFilter.value = ''
  visitDateFilter.value = ''
  statusFilter.value = ''
  page.value = 1
  loadList()
}

/** 分页切换 */
/** 删除预约记录 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除该预约记录吗？患者：${row.user_name || '未知'}，预约日期：${row.visit_date || ''}`,
      '提示',
      { type: 'warning' },
    )
    await request.delete(`/appointments/admin/${row.id}`)
    ElMessage.success('删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    loadList()
  } catch { /* */ }
}

onMounted(() => {
  loadDepartments()
  loadList()
})
</script>

<template>
  <div>
    <h2 class="page-title">预约管理</h2>
    <div class="modern-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索患者 / 医生 / 备注"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        />
        <el-select
          v-model="departmentFilter"
          placeholder="选择科室"
          clearable
          style="width: 160px"
        >
          <el-option
            v-for="d in departments"
            :key="d.id"
            :label="d.name"
            :value="d.id"
          />
        </el-select>
        <el-date-picker
          v-model="visitDateFilter"
          type="date"
          placeholder="预约日期"
          value-format="YYYY-MM-DD"
          clearable
          style="width: 160px"
        />
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          clearable
          style="width: 140px"
        >
          <el-option label="待确认" :value="0" />
          <el-option label="已确认" :value="1" />
          <el-option label="已完成" :value="2" />
          <el-option label="已取消" :value="3" />
        </el-select>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="user_name" label="患者" min-width="100" />
        <el-table-column prop="doctor_name" label="医生" min-width="100" />
        <el-table-column prop="department_name" label="科室" min-width="120" />
        <el-table-column prop="visit_date" label="预约日期" min-width="120" />
        <el-table-column prop="time_slot" label="时段" min-width="100" />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ statusMap[row.status] ?? '待确认' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="create_time" label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !list.length" description="暂无预约数据" />

      <!-- 分页 -->
      <AppPagination
        v-model:page="page"
        v-model:page-size="pageSize"
        :total="total"
        @change="loadList"
      />
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
