<template>
  <div class="bg-white rounded-xl border p-6 hover:shadow-md transition">
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-medium text-gray-500">{{ label }}</span>
      <span :class="iconBg" class="w-10 h-10 rounded-lg flex items-center justify-center">
        <slot name="icon" />
      </span>
    </div>
    <div class="text-3xl font-bold text-gray-900">{{ formattedValue }}</div>
    <div v-if="sub" class="text-xs text-gray-500 mt-1">{{ sub }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  label: string;
  value: number;
  sub?: string;
  iconBg?: string;
}>();

const formattedValue = computed(() => props.value.toLocaleString());
</script>
