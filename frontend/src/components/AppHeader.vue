<template>
  <header class="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="text-xl font-bold text-primary-700 hover:text-primary-600 shrink-0">
        {{ store.settings.blog_title }}
      </router-link>

      <!-- Desktop Nav -->
      <nav class="hidden md:flex items-center gap-6 text-sm font-medium text-gray-600">
        <router-link to="/" class="hover:text-primary-600 transition-colors">首页</router-link>
        <router-link to="/posts" class="hover:text-primary-600 transition-colors">文章</router-link>
        <div v-for="cat in store.categories.slice(0, 4)" :key="cat.id">
          <router-link :to="`/categories/${cat.slug}`" class="hover:text-primary-600 transition-colors">
            {{ cat.name }}
          </router-link>
        </div>
      </nav>

      <!-- Right: Search + Mobile Toggle -->
      <div class="flex items-center gap-3">
        <div class="hidden sm:block relative">
          <input
            v-model="query"
            @keyup.enter="doSearch"
            @focus="showSearch = true"
            @blur="handleBlur"
            placeholder="搜索文章..."
            class="w-48 pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent"
          />
          <svg class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 text-gray-600 hover:text-gray-900">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile Nav -->
    <div v-if="mobileOpen" class="md:hidden border-t bg-white px-4 py-4 space-y-3">
      <router-link @click="mobileOpen=false" to="/" class="block py-2 font-medium">首页</router-link>
      <router-link @click="mobileOpen=false" to="/posts" class="block py-2 font-medium">全部文章</router-link>
      <div v-for="cat in store.categories" :key="cat.id">
        <router-link @click="mobileOpen=false" :to="`/categories/${cat.slug}`" class="block py-2 font-medium">{{ cat.name }}</router-link>
      </div>
      <div class="pt-2">
        <input v-model="query" @keyup.enter="doSearch" placeholder="搜索文章..." class="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAppStore } from "@/stores/app";

const store = useAppStore();
const router = useRouter();
const query = ref("");
const showSearch = ref(false);
const mobileOpen = ref(false);

function doSearch() {
  if (query.value.trim()) {
    store.setSearch(query.value.trim());
    router.push({ name: "search", query: { q: query.value.trim() } });
    showSearch.value = false;
    mobileOpen.value = false;
  }
}
function handleBlur() {
  setTimeout(() => (showSearch.value = false), 200);
}
</script>
