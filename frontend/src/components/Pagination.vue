<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 mt-8">
    <button
      @click="$emit('page-change', currentPage - 1)"
      :disabled="currentPage <= 1"
      class="px-3 py-2 rounded-lg text-sm border disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 transition"
    >
      上一页
    </button>

    <button
      v-for="p in visiblePages"
      :key="p"
      @click="$emit('page-change', p)"
      :class="[
        'px-3 py-2 rounded-lg text-sm border transition min-w-[40px]',
        p === currentPage
          ? 'bg-primary-600 text-white border-primary-600'
          : 'hover:bg-gray-100',
      ]"
    >
      {{ p }}
    </button>

    <button
      @click="$emit('page-change', currentPage + 1)"
      :disabled="currentPage >= totalPages"
      class="px-3 py-2 rounded-lg text-sm border disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 transition"
    >
      下一页
    </button>
    <span class="text-xs text-gray-500 ml-3">共 {{ total }} 篇</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  currentPage: number;
  totalPages: number;
  total: number;
}>();
defineEmits<{ 'page-change': [page: number] }>();

const visiblePages = computed(() => {
  const pages: number[] = [];
  const start = Math.max(1, props.currentPage - 2);
  const end = Math.min(props.totalPages, start + 4);
  for (let i = start; i <= end; i++) pages.push(i);
  return pages;
});
</script>
