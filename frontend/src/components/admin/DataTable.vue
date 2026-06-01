<template>
  <div class="bg-white rounded-xl border overflow-hidden">
    <!-- Header -->
    <div v-if="$slots.header" class="px-6 py-4 border-b flex items-center justify-between">
      <slot name="header" />
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th v-if="selectable" class="w-10 px-4 py-3">
              <input type="checkbox" :checked="allSelected" @change="toggleAll" class="rounded" />
            </th>
            <th v-for="col in columns" :key="col.key" :class="['px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider', col.class]">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="row in rows" :key="row.id" class="hover:bg-gray-50 transition">
            <td v-if="selectable" class="px-4 py-3">
              <input type="checkbox" :checked="isSelected(row.id)" @change="toggleRow(row.id)" class="rounded" />
            </td>
            <td v-for="col in columns" :key="col.key" :class="['px-4 py-3', col.class]">
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                {{ row[col.key] }}
              </slot>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td :colspan="columns.length + (selectable ? 1 : 0)" class="px-4 py-16 text-center text-gray-400">
              暂无数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="px-6 py-3 border-t bg-gray-50">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

interface Column {
  key: string;
  label: string;
  class?: string;
}

const props = defineProps<{
  columns: Column[];
  rows: any[];
  selectable?: boolean;
}>();

const emit = defineEmits<{ 'selection-change': [ids: number[]] }>();

const selected = ref<Set<number>>(new Set());

const allSelected = computed(() => props.rows.length > 0 && selected.value.size === props.rows.length);
const isSelected = (id: number) => selected.value.has(id);

function toggleAll() {
  if (allSelected.value) {
    selected.value.clear();
  } else {
    props.rows.forEach((r) => selected.value.add(r.id));
  }
  emit("selection-change", [...selected.value]);
}

function toggleRow(id: number) {
  if (selected.value.has(id)) selected.value.delete(id);
  else selected.value.add(id);
  emit("selection-change", [...selected.value]);
}
</script>
