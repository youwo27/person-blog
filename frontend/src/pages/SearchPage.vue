<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <Breadcrumb :items="[{ label: '搜索' }]" />

    <!-- Search Input -->
    <div class="mb-8">
      <div class="relative max-w-2xl">
        <input
          v-model="query"
          @keyup.enter="doSearch"
          placeholder="输入关键词搜索文章..."
          autofocus
          class="w-full pl-12 pr-4 py-3.5 text-lg border-2 border-gray-300 rounded-xl focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
        />
        <svg class="absolute left-4 top-4 w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Results -->
    <LoadingSpinner v-if="loading" />
    <template v-else-if="searched">
      <div class="mb-4 text-sm text-gray-500">
        搜索 "<span class="font-medium text-gray-900">{{ searchedQuery }}</span>" — 找到 {{ total }} 篇结果
      </div>
      <EmptyState v-if="!results.length" title="没有找到相关文章" description="换个关键词试试" />
      <div v-else class="space-y-6">
        <article
          v-for="post in results"
          :key="post.id"
          class="flex flex-col sm:flex-row gap-4 p-5 bg-white rounded-xl border hover:shadow-md transition"
        >
          <router-link :to="`/posts/${post.slug}`" class="shrink-0 sm:w-48 h-32 rounded-lg bg-gray-100 overflow-hidden">
            <img
              v-if="post.cover_image_url"
              :src="post.cover_image_url"
              :alt="post.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-300">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </router-link>
          <div class="flex-1 min-w-0">
            <router-link :to="`/posts/${post.slug}`">
              <h3 class="text-lg font-semibold mb-1.5 hover:text-primary-600 transition line-clamp-1">{{ post.title }}</h3>
            </router-link>
            <p class="text-sm text-gray-600 leading-relaxed mb-2 line-clamp-2">{{ post.excerpt }}</p>
            <div class="flex items-center gap-2 text-xs text-gray-500">
              <span>{{ post.author?.display_name }}</span>
              <span>·</span>
              <span v-if="post.published_at">{{ formatDate(post.published_at) }}</span>
              <span>·</span>
              <span>{{ post.view_count }} 浏览</span>
            </div>
          </div>
        </article>

        <Pagination
          :current-page="currentPage"
          :total-pages="Math.ceil(total / 12)"
          :total="total"
          @page-change="(p: number) => fetchResults(p)"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { postsApi } from "@/api";
import axios from "axios";
import { useAppStore } from "@/stores/app";
import type { Post } from "@/types";
import Breadcrumb from "@/components/Breadcrumb.vue";
import Pagination from "@/components/Pagination.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const route = useRoute();
const router = useRouter();
const store = useAppStore();

const query = ref((route.query.q as string) || store.searchQuery || "");
const searchedQuery = ref("");
const searched = ref(false);
const results = ref<Post[]>([]);
const total = ref(0);
const currentPage = ref(1);
const loading = ref(false);

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

async function fetchResults(page: number = 1) {
  if (!query.value.trim()) return;
  loading.value = true;
  currentPage.value = page;
  searchedQuery.value = query.value.trim();
  searched.value = true;
  store.setSearch(query.value.trim());

  try {
    const { data } = await postsApi.list({ page, page_size: 12, search: query.value.trim() });
    if (data.success) {
      results.value = data.results || [];
      total.value = data.count || 0;
    }
  } catch {
    results.value = [];
  } finally {
    loading.value = false;
  }
}

function doSearch() {
  router.replace({ name: "search", query: { q: query.value.trim() } });
  fetchResults(1);
}

onMounted(() => {
  if (query.value.trim()) doSearch();
});

watch(() => route.query.q, (newQ) => {
  if (newQ && typeof newQ === "string") {
    query.value = newQ;
    doSearch();
  }
});
</script>
