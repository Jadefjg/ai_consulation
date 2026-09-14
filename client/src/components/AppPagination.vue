<script setup lang="ts">
/**
 * 统一列表底部分页栏
 * 布局：共 N 条 | 上一页 | 页码 | 下一页 | 每页条数 | 跳转
 */
const props = defineProps({
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100],
  },
})

const emit = defineEmits(['update:page', 'update:pageSize', 'change'])

function onPageChange(value) {
  emit('update:page', value)
  emit('change', value)
}

function onSizeChange(value) {
  emit('update:pageSize', value)
  emit('update:page', 1)
  emit('change', 1)
}
</script>

<template>
  <div v-if="total > 0" class="app-pagination">
    <el-pagination
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      :page-sizes="pageSizes"
      layout="total, prev, pager, next, sizes, jumper"
      background
      @current-change="onPageChange"
      @size-change="onSizeChange"
    />
  </div>
</template>

<style scoped>
.app-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
