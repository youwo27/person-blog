<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50" @click="$emit('cancel')"></div>
      <div class="relative bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
        <h3 class="text-lg font-semibold mb-2">{{ title }}</h3>
        <p class="text-sm text-gray-600 mb-6">{{ message }}</p>
        <div class="flex justify-end gap-3">
          <button @click="$emit('cancel')" class="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 transition">取消</button>
          <button @click="$emit('confirm')" :class="confirmClass" class="px-4 py-2 text-sm rounded-lg text-white transition">
            {{ confirmText || '确认' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
  title: string;
  message: string;
  confirmText?: string;
  confirmClass?: string;
}>();
defineEmits<{ confirm: []; cancel: [] }>();
</script>
