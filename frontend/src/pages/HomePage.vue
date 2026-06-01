<template>
  <div>
    <!-- Hero -->
    <section class="bg-gradient-to-br from-primary-600 via-primary-700 to-indigo-800 text-white">
      <div class="max-w-7xl mx-auto px-4 py-20 md:py-28 text-center">
        <h1 class="text-4xl md:text-5xl font-bold mb-4 tracking-tight">{{ store.settings.blog_title }}</h1>
        <p class="text-lg md:text-xl text-primary-100 max-w-2xl mx-auto mb-8">{{ store.settings.blog_description }}</p>
        <div class="flex justify-center gap-4">
          <router-link to="/posts" class="px-6 py-3 bg-white text-primary-700 font-medium rounded-lg hover:bg-gray-100 transition shadow-lg">
            浏览文章
          </router-link>
          <router-link to="/search" class="px-6 py-3 border-2 border-white/40 text-white font-medium rounded-lg hover:bg-white/10 transition">
            搜索
          </router-link>
        </div>
      </div>
    </section>

    <div class="max-w-7xl mx-auto px-4 py-12">
      <!-- Featured Posts -->
      <section v-if="featured.length" class="mb-12">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold">精选文章</h2>
          <router-link to="/posts?featured=true" class="text-sm text-primary-600 hover:underline">查看全部 →</router-link>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <PostCard v-for="post in featured" :key="post.id" :post="post" />
        </div>
      </section>

      <!-- Latest Posts -->
      <section>
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold">最新文章</h2>
          <router-link to="/posts" class="text-sm text-primary-600 hover:underline">查看全部 →</router-link>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <PostCard v-for="post in latest" :key="post.id" :post="post" />
        </div>
        <LoadingSpinner v-if="loading" />
      </section>

      <!-- Categories + Tags sidebar (below on mobile) -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-8 mt-16 pt-12 border-t">
        <div class="lg:col-span-3">
          <h3 class="text-lg font-semibold mb-4">文章分类</h3>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
            <router-link
              v-for="cat in store.categories"
              :key="cat.id"
              :to="`/categories/${cat.slug}`"
              class="flex items-center justify-between p-4 bg-white border rounded-lg hover:border-primary-300 hover:shadow-sm transition group"
            >
              <span class="font-medium text-gray-700 group-hover:text-primary-600">{{ cat.name }}</span>
              <span class="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">{{ cat.post_count }}</span>
            </router-link>
          </div>
        </div>
        <div>
          <h3 class="text-lg font-semibold mb-4">热门标签</h3>
          <div class="flex flex-wrap gap-2">
            <router-link
              v-for="tag in store.tags.slice(0, 15)"
              :key="tag.id"
              :to="`/tags/${tag.slug}`"
              class="px-3 py-1.5 bg-white border rounded-full text-sm text-gray-600 hover:border-primary-400 hover:text-primary-600 transition"
            >
              {{ tag.name }} <span class="text-xs text-gray-400">({{ tag.post_count }})</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { postsApi } from "@/api";
import { useAppStore } from "@/stores/app";
import type { Post } from "@/types";
import PostCard from "@/components/PostCard.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";

const store = useAppStore();
const featured = ref<Post[]>([]);
const latest = ref<Post[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const [featRes, listRes] = await Promise.all([
      postsApi.featured(),
      postsApi.list({ page_size: 6, ordering: "-published_at" }),
    ]);
    if (featRes.data.success && featRes.data.results) featured.value = featRes.data.results;
    if (listRes.data.success && listRes.data.results) latest.value = listRes.data.results;
  } finally {
    loading.value = false;
  }
});
</script>
