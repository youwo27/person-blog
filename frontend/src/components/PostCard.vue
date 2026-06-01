<template>
  <article class="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow group">
    <!-- Cover Image -->
    <router-link :to="`/posts/${post.slug}`" class="block aspect-[16/9] bg-gray-100 overflow-hidden">
      <img
        v-if="post.cover_image_url"
        :src="post.cover_image_url"
        :alt="post.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-300">
        <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
    </router-link>

    <!-- Body -->
    <div class="p-5">
      <!-- Category + Date -->
      <div class="flex items-center gap-2 text-xs text-gray-500 mb-2">
        <router-link
          v-if="post.category"
          :to="`/categories/${post.category.slug}`"
          class="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-full font-medium hover:bg-primary-100"
        >
          {{ post.category.name }}
        </router-link>
        <span v-if="post.published_at">{{ formatDate(post.published_at) }}</span>
      </div>

      <!-- Title -->
      <router-link :to="`/posts/${post.slug}`" class="block group/title">
        <h3 class="text-lg font-semibold leading-snug mb-2 group-hover/title:text-primary-600 transition-colors line-clamp-2">
          {{ post.title }}
        </h3>
      </router-link>

      <!-- Excerpt -->
      <p class="text-sm text-gray-600 leading-relaxed mb-3 line-clamp-2">{{ post.excerpt }}</p>

      <!-- Footer -->
      <div class="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-xs font-medium">
            {{ post.author?.display_name?.charAt(0) || '?' }}
          </div>
          <span>{{ post.author?.display_name }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
            {{ post.view_count }}
          </span>
          <span>{{ post.reading_time_minutes }} 分钟阅读</span>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { Post } from "@/types";

defineProps<{ post: Post }>();

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
</script>
