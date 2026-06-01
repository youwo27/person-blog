<template>
  <nav class="flex items-center gap-1.5 text-sm text-gray-500 mb-6" aria-label="Breadcrumb">
    <router-link to="/" class="hover:text-primary-600 transition-colors">首页</router-link>
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
    </svg>
    <template v-for="(item, idx) in items" :key="idx">
      <router-link v-if="item.to && idx < items.length - 1" :to="item.to" class="hover:text-primary-600 transition-colors">
        {{ item.label }}
      </router-link>
      <span v-else class="text-gray-900 font-medium">{{ item.label }}</span>
      <svg v-if="idx < items.length - 1" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </template>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  items: { label: string; to?: string }[];
}>();
</script>
