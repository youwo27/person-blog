<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <LoadingSpinner v-if="loading" />
    <template v-else-if="post">
      <Breadcrumb :items="breadcrumbItems" />

      <!-- Header -->
      <header class="mb-8">
        <div class="flex flex-wrap items-center gap-2 mb-3 text-xs text-gray-500">
          <router-link
            v-if="post.category"
            :to="`/categories/${post.category.slug}`"
            class="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full font-medium hover:bg-primary-100"
          >
            {{ post.category.name }}
          </router-link>
          <span v-if="post.published_at">{{ formatDate(post.published_at) }}</span>
          <span>· {{ post.reading_time_minutes }} 分钟阅读</span>
          <span>· {{ post.view_count }} 次浏览</span>
          <span v-if="post.status !== 'PUBLISHED'" class="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full font-medium">{{ post.status }}</span>
        </div>

        <h1 class="text-3xl md:text-4xl font-bold mb-4 leading-tight">{{ post.title }}</h1>

        <div class="flex items-center gap-3 py-4 border-y border-gray-200">
          <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm">
            {{ post.author?.display_name?.charAt(0) || '?' }}
          </div>
          <div>
            <div class="text-sm font-medium text-gray-900">{{ post.author?.display_name }}</div>
            <div class="text-xs text-gray-500">作者</div>
          </div>
          <div class="ml-auto flex flex-wrap gap-1.5">
            <router-link
              v-for="tag in post.tags"
              :key="tag.id"
              :to="`/tags/${tag.slug}`"
              class="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-xs text-gray-600 transition"
            >
              #{{ tag.name }}
            </router-link>
          </div>
        </div>

        <!-- Cover Image -->
        <img
          v-if="post.cover_image_url"
          :src="post.cover_image_url"
          :alt="post.title"
          class="w-full rounded-xl mt-6 object-cover max-h-[500px]"
        />
      </header>

      <!-- Content -->
      <article class="post-content mb-10" v-html="post.content_html"></article>

      <!-- Prev / Next -->
      <nav class="grid grid-cols-1 sm:grid-cols-2 gap-4 py-6 border-t border-b mb-10">
        <div v-if="post.prev_post">
          <span class="text-xs text-gray-500">← 上一篇</span>
          <router-link :to="`/posts/${post.prev_post.slug}`" class="block text-sm font-medium text-primary-600 hover:underline mt-0.5">
            {{ post.prev_post.title }}
          </router-link>
        </div>
        <div v-if="post.next_post" class="sm:text-right">
          <span class="text-xs text-gray-500">下一篇 →</span>
          <router-link :to="`/posts/${post.next_post.slug}`" class="block text-sm font-medium text-primary-600 hover:underline mt-0.5">
            {{ post.next_post.title }}
          </router-link>
        </div>
      </nav>

      <!-- Comments -->
      <CommentSection :post-id="post.id" :slug="post.slug" />
    </template>

    <!-- Empty / Not Found -->
    <EmptyState v-else title="文章不存在" description="该文章可能已被删除或暂未发布" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { postsApi } from "@/api";
import { useAppStore } from "@/stores/app";
import type { PostDetail } from "@/types";
import Breadcrumb from "@/components/Breadcrumb.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";
import CommentSection from "@/components/CommentSection.vue";

const route = useRoute();
const store = useAppStore();
const post = ref<PostDetail | null>(null);
const loading = ref(true);

const breadcrumbItems = computed(() => {
  const items: { label: string; to?: string }[] = [];
  items.push({ label: "全部文章", to: "/posts" });
  if (post.value?.category) {
    items.push({ label: post.value.category.name, to: `/categories/${post.value.category.slug}` });
  }
  items.push({ label: post.value?.title || "文章" });
  return items;
});

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

onMounted(async () => {
  try {
    const { data } = await postsApi.get(route.params.slug as string);
    if (data.success && data.data) post.value = data.data;
  } catch {
    post.value = null;
  } finally {
    loading.value = false;
  }
});
</script>
