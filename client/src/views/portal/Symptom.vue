<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const symptomInput = ref('')
const symptoms = ref([])
const inferResult = ref(null)
const diseaseDetail = ref(null)
const showDetail = ref(false)
const loading = ref(false)

/** 解析推理结果列表（兼容数组与对象两种返回格式） */
const inferResultList = computed(() => {
  const data = inferResult.value
  if (!data) return []
  if (Array.isArray(data)) return data
  return data.diseases || data.results || []
})

/** 获取疾病名称 */
function getDiseaseName(row) {
  return row.name || row.disease || '-'
}

/** 计算匹配度百分比 */
function getMatchPercent(row) {
  const probability = row.probability ?? row.score
  if (probability != null && probability <= 1) {
    return Math.round(probability * 100)
  }
  const total = symptoms.value.length || 1
  return Math.round(((row.match_count || 0) / total) * 100)
}

/** 添加症状标签 */
function addSymptom() {
  const val = symptomInput.value.trim()
  if (!val) return
  if (!symptoms.value.includes(val)) {
    symptoms.value.push(val)
  }
  symptomInput.value = ''
}

/** 移除症状 */
function removeSymptom(idx) {
  symptoms.value.splice(idx, 1)
}

/** 知识图谱推理 */
async function handleInfer() {
  if (!symptoms.value.length) {
    ElMessage.warning('请至少添加一个症状')
    return
  }
  loading.value = true
  diseaseDetail.value = null
  try {
    const res = await request.post('/graph/infer', { symptoms: symptoms.value })
    inferResult.value = res.data
    if (!inferResultList.value.length) {
      ElMessage.info('未找到匹配疾病，请尝试使用常见表述，如：头痛、发热')
    }
  } catch {
    inferResult.value = null
  } finally {
    loading.value = false
  }
}

/** 查看疾病详情 */
async function viewDisease(name) {
  try {
    const res = await request.get(`/graph/disease/${encodeURIComponent(name)}`)
    diseaseDetail.value = res.data
    showDetail.value = true
  } catch {
    diseaseDetail.value = null
  }
}
</script>

<template>
  <div class="symptom-page">
    <h2 class="page-title">症状知识图谱推理</h2>

    <div class="modern-card input-section">
      <h3>输入症状</h3>
      <div class="symptom-input-row">
        <el-input
          v-model="symptomInput"
          placeholder="输入症状后按回车添加，如：头痛、发热"
          @keyup.enter="addSymptom"
        />
        <el-button type="primary" class="gradient-btn" @click="addSymptom">添加</el-button>
        <el-button type="primary" class="gradient-btn" :loading="loading" @click="handleInfer">
          开始推理
        </el-button>
      </div>
      <div class="symptom-tags">
        <el-tag
          v-for="(s, idx) in symptoms"
          :key="s"
          closable
          type="primary"
          effect="plain"
          size="large"
          @close="removeSymptom(idx)"
        >
          {{ s }}
        </el-tag>
      </div>
    </div>

    <!-- 推理结果 -->
    <div v-if="inferResult !== null" class="modern-card result-section">
      <h3>推理结果</h3>
      <el-table :data="inferResultList" class="adaptive-table" stripe>
        <el-table-column label="可能疾病" min-width="150">
          <template #default="{ row }">{{ getDiseaseName(row) }}</template>
        </el-table-column>
        <el-table-column label="匹配度" min-width="120">
          <template #default="{ row }">
            <el-progress :percentage="getMatchPercent(row)" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="department" label="建议科室" min-width="120" />
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDisease(getDiseaseName(row))">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 疾病详情 -->
    <el-drawer
      v-model="showDetail"
      :title="diseaseDetail?.name || diseaseDetail?.disease || '疾病详情'"
      size="480px"
    >
      <template v-if="diseaseDetail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="疾病名称">
            {{ diseaseDetail.name || diseaseDetail.disease }}
          </el-descriptions-item>
          <el-descriptions-item label="所属科室">{{ diseaseDetail.department || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ diseaseDetail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="常见症状">
            <el-tag v-for="s in (diseaseDetail.symptoms || [])" :key="s" size="small" style="margin: 2px">{{ s }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="治疗建议">{{ diseaseDetail.treatment || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.input-section h3,
.result-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.symptom-input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.symptom-input-row .el-input {
  flex: 1;
}

.symptom-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.result-section {
  margin-top: 20px;
}
</style>
