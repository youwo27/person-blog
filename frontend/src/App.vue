<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <main class="flex-1">
      <router-view />
    </main>
    <AppFooter />
    <SearchModal ref="searchModal" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppHeader from "@/components/AppHeader.vue";
import AppFooter from "@/components/AppFooter.vue";
import SearchModal from "@/components/SearchModal.vue";
import { useAppStore } from "@/stores/app";

const store = useAppStore();
const searchModal = ref<InstanceType<typeof SearchModal>>();
onMounted(() => store.init());

// Global access to open search modal
(window as any).__openSearch = () => searchModal.value?.open();
</script>
