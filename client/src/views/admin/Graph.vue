<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import request from '@/utils/request'

use([CanvasRenderer, GraphChart, TooltipComponent, LegendComponent])

const keyword = ref('')
const entity = ref('')
const isFullGraph = ref(true)
const searchResults = ref([])
const graphOption = ref({})
const loading = ref(false)

/** 常见症状（快捷搜索） */
const commonSymptoms = [
  '头痛', '发热', '咳嗽', '乏力', '胸闷', '腹痛',
  '头晕', '恶心', '呕吐', '腹泻', '咽痛', '流涕',
]

/** 常见疾病（快捷搜索） */
const commonDiseases = [
  '感冒', '高血压', '糖尿病', '胃炎', '肺炎',
  '支气管炎', '冠心病', '脑卒中', '过敏',
]

/** 关系类型中文映射 */
const relationLabelMap = {
  HAS_SYMPTOM: '有症状',
  BELONGS_TO: '所属科室',
  RECOMMEND_DRUG: '推荐药物',
  NEED_CHECK: '需检查',
  ACCOMPANY_WITH: '并发症',
  SHOULD_EAT: '宜吃',
  AVOID_EAT: '忌吃',
}

/** 节点类型映射为图例分类索引 */
function mapNodeCategory(label) {
  if (label === 'Disease') return 0
  if (label === 'Symptom') return 1
  return 2
}

/** 节点类型中文名 */
function mapNodeTypeName(label) {
  const map = {
    Disease: '疾病',
    Symptom: '症状',
    Department: '科室',
    Drug: '药物',
    Check: '检查',
    Food: '食物',
  }
  return map[label] || label || '其他'
}

/** 搜索实体 */
async function handleSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  try {
    const res = await request.get('/graph/search', { params: { keyword: keyword.value } })
    searchResults.value = res.data?.items || res.data || []
  } catch {
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

/** 点击常见标签快捷搜索 */
function quickSearch(name) {
  keyword.value = name
  handleSearch()
  loadSubgraph(name)
}

/** 加载完整图谱 */
async function loadFullGraph() {
  entity.value = ''
  isFullGraph.value = true
  loading.value = true
  try {
    const res = await request.get('/graph/full')
    graphOption.value = buildGraphOption(res.data, true)
  } catch {
    graphOption.value = {}
  } finally {
    loading.value = false
  }
}

/** 加载子图 */
async function loadSubgraph(name) {
  entity.value = name
  isFullGraph.value = false
  loading.value = true
  try {
    const res = await request.get('/graph/subgraph', { params: { entity: name } })
    graphOption.value = buildGraphOption(res.data, false)
  } catch {
    graphOption.value = {}
  } finally {
    loading.value = false
  }
}

/** 构建 ECharts 关系图配置 */
function buildGraphOption(data, full = false) {
  const nodes = (data?.nodes || []).map((n) => {
    const categoryLabel = n.category || n.type || ''
    const catIdx = mapNodeCategory(categoryLabel)
    return {
      id: String(n.id || n.name),
      name: n.name || n.label,
      symbolSize: categoryLabel === 'Disease' ? 50 : categoryLabel === 'Symptom' ? 35 : 28,
      category: catIdx,
      label: { show: true, fontSize: full ? 9 : 11 },
    }
  })
  const links = (data?.edges || data?.links || []).map((e) => {
    const rel = e.relation || ''
    const relText = relationLabelMap[rel] || rel
    return {
      source: String(e.source || e.from),
      target: String(e.target || e.to),
      label: {
        show: true,
        formatter: relText,
        fontSize: full ? 8 : 10,
      },
    }
  })
  return {
    tooltip: {
      formatter(params) {
        if (params.dataType === 'node') {
          const node = (data?.nodes || []).find((n) => String(n.id || n.name) === params.data.id)
          const cat = node?.category || node?.type || ''
          return `${params.data.name}<br/>类型：${mapNodeTypeName(cat)}`
        }
        if (params.dataType === 'edge') {
          return params.data.label?.formatter || ''
        }
        return ''
      },
    },
    legend: { data: ['疾病', '症状', '其他'], bottom: 0 },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: {
        repulsion: full ? 600 : 300,
        edgeLength: full ? [60, 120] : [80, 150],
        gravity: full ? 0.05 : 0.1,
      },
      categories: [
        { name: '疾病', itemStyle: { color: '#b56bc4' } },
        { name: '症状', itemStyle: { color: '#cc5084' } },
        { name: '其他', itemStyle: { color: '#e07098' } },
      ],
      data: nodes,
      links,
      lineStyle: { color: '#ccc', curveness: 0.2 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
    }],
  }
}

/** 是否有图数据 */
const hasGraph = computed(() => {
  const s = graphOption.value?.series
  return s && s[0]?.data?.length > 0
})

/** 页面加载时默认展示完整图谱 */
onMounted(() => {
  loadFullGraph()
})
</script>

<template>
  <div class="graph-page">
    <h2 class="page-title">知识图谱可视化</h2>

    <!-- 搜索区域 -->
    <div class="modern-card search-section">
      <div class="search-row">
        <el-input v-model="keyword" placeholder="搜索实体（疾病、症状等）" clearable @keyup.enter="handleSearch" />
        <el-button type="primary" class="gradient-btn" :loading="loading" @click="handleSearch">搜索</el-button>
      </div>

      <!-- 常见症状快捷入口 -->
      <div class="common-tags">
        <span class="common-label">常见症状：</span>
        <el-tag
          v-for="name in commonSymptoms"
          :key="'sym-' + name"
          class="common-tag"
          effect="plain"
          @click="quickSearch(name)"
        >
          {{ name }}
        </el-tag>
      </div>

      <!-- 常见疾病快捷入口 -->
      <div class="common-tags">
        <span class="common-label">常见疾病：</span>
        <el-tag
          v-for="name in commonDiseases"
          :key="'dis-' + name"
          class="common-tag disease-tag"
          effect="plain"
          @click="quickSearch(name)"
        >
          {{ name }}
        </el-tag>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length" class="search-results">
        <span class="common-label">搜索结果：</span>
        <el-tag
          v-for="item in searchResults"
          :key="item.name || item.id"
          class="result-tag"
          effect="plain"
          @click="loadSubgraph(item.name || item.label)"
        >
          {{ item.name || item.label }} ({{ mapNodeTypeName(item.label) }})
        </el-tag>
      </div>
    </div>

    <!-- 图谱可视化（自适应剩余高度） -->
    <div class="modern-card graph-section">
      <div class="graph-header">
        <span v-if="isFullGraph">当前视图：<strong>全部图谱</strong>（含所有节点与关系）</span>
        <span v-else>
          当前实体：<strong>{{ entity }}</strong>
          <el-button link type="primary" class="back-btn" @click="loadFullGraph">返回全图</el-button>
        </span>
      </div>
      <div class="chart-container" v-loading="loading">
        <v-chart v-if="hasGraph" :option="graphOption" autoresize class="graph-chart" />
        <el-empty v-else description="暂无图谱数据" class="graph-empty" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 页面整体高度自适应到浏览器底部（扣除顶栏60px + 内边距40px） */
.graph-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  min-height: 0;
}

.graph-page .page-title {
  flex-shrink: 0;
  margin-bottom: 16px;
}

.search-section {
  flex-shrink: 0;
  margin-bottom: 16px;
}

.search-row {
  display: flex;
  gap: 12px;
}

.search-row .el-input {
  flex: 1;
}

.common-tags {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.common-label {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
  min-width: 72px;
}

.common-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.common-tag:hover {
  background: var(--color-brand);
  color: #fff;
  border-color: var(--color-brand);
}

.disease-tag:hover {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.search-results {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px dashed #e8e8e8;
}

.result-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.result-tag:hover {
  background: var(--color-accent);
  color: #fff;
}

/* 图谱区域占据剩余高度 */
.graph-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: 0;
  overflow: hidden;
}

.graph-header {
  flex-shrink: 0;
  margin-bottom: 12px;
  font-size: 14px;
}

.back-btn {
  margin-left: 12px;
}

.chart-container {
  flex: 1;
  min-height: 280px;
  position: relative;
}

.graph-chart {
  width: 100%;
  height: 100%;
}

.graph-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
