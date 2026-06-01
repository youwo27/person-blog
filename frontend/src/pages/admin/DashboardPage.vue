<template>
  <div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <StatsCard label="文章总数" :value="stats.totalPosts" sub="含草稿和归档" icon-bg="bg-blue-100 text-blue-600">
        <template #icon><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></template>
      </StatsCard>
      <StatsCard label="已发布" :value="stats.publishedPosts" sub="公开可见" icon-bg="bg-green-100 text-green-600">
        <template #icon><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></template>
      </StatsCard>
      <StatsCard label="总评论" :value="stats.totalComments" :sub="`${stats.pendingComments} 条待审核`" icon-bg="bg-orange-100 text-orange-600">
        <template #icon><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg></template>
      </StatsCard>
      <StatsCard label="总浏览" :value="stats.totalViews" sub="所有文章" icon-bg="bg-purple-100 text-purple-600">
        <template #icon><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg></template>
      </StatsCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Recent Posts -->
      <div class="lg:col-span-2 bg-white rounded-xl border">
        <div class="px-6 py-4 border-b flex items-center justify-between">
          <h3 class="font-semibold">最近文章</h3>
          <router-link to="/admin/posts" class="text-xs text-primary-600 hover:underline">全部 →</router-link>
        </div>
        <div class="divide-y">
          <div v-for="post in recentPosts" :key="post.id" class="px-6 py-3 flex items-center gap-4 hover:bg-gray-50">
            <div class="flex-1 min-w-0">
              <router-link :to="`/admin/posts/${post.slug}/edit`" class="text-sm font-medium hover:text-primary-600 truncate block">{{ post.title }}</router-link>
              <div class="text-xs text-gray-500 mt-0.5">{{ post.author?.display_name }} · {{ formatDate(post.created_at) }}</div>
            </div>
            <span :class="statusBadge(post.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ statusLabel(post.status) }}</span>
          </div>
          <div v-if="!recentPosts.length" class="px-6 py-8 text-center text-gray-400 text-sm">暂无文章</div>
        </div>
      </div>

      <!-- Recent Comments -->
      <div class="bg-white rounded-xl border">
        <div class="px-6 py-4 border-b flex items-center justify-between">
          <h3 class="font-semibold">最近评论</h3>
          <router-link to="/admin/comments" class="text-xs text-primary-600 hover:underline">全部 →</router-link>
        </div>
        <div class="divide-y">
          <div v-for="c in recentComments" :key="c.id" class="px-6 py-3 hover:bg-gray-50">
            <div class="text-sm line-clamp-2 mb-1" v-html="c.content_html"></div>
            <div class="text-xs text-gray-500 flex items-center justify-between">
              <span>{{ c.author?.display_name }}</span>
              <span v-if="!c.is_approved" class="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs">待审核</span>
            </div>
          </div>
          <div v-if="!recentComments.length" class="px-6 py-8 text-center text-gray-400 text-sm">暂无评论</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { postsApi, commentsApi } from "@/api";
import type { Post, Comment } from "@/types";
import StatsCard from "@/components/admin/StatsCard.vue";

const stats = ref({ totalPosts: 0, publishedPosts: 0, totalComments: 0, pendingComments: 0, totalViews: 0 });
const recentPosts = ref<Post[]>([]);
const recentComments = ref<Comment[]>([]);

function statusBadge(s: string) { return s === "PUBLISHED" ? "bg-green-100 text-green-700" : s === "DRAFT" ? "bg-gray-100 text-gray-600" : s === "ARCHIVED" ? "bg-red-100 text-red-600" : "bg-blue-100 text-blue-600"; }
function statusLabel(s: string) { return s === "PUBLISHED" ? "已发布" : s === "DRAFT" ? "草稿" : s === "ARCHIVED" ? "已归档" : "定时"; }
function formatDate(d: string) { return new Date(d).toLocaleDateString("zh-CN"); }

onMounted(async () => {
  try {
    const [postRes, commentRes] = await Promise.all([
      postsApi.list({ page_size: 100 }),
      commentsApi.list(),
    ]);
    if (postRes.data.success) {
      const all = postRes.data.results || [];
      stats.value.totalPosts = postRes.data.count || all.length;
      stats.value.publishedPosts = all.filter((p: Post) => p.status === "PUBLISHED").length;
      stats.value.totalViews = all.reduce((sum: number, p: Post) => sum + p.view_count, 0);
      recentPosts.value = all.slice(0, 8);
    }
    if (commentRes.data.success) {
      const all = commentRes.data.results || [];
      stats.value.totalComments = all.length;
      stats.value.pendingComments = all.filter((c: Comment) => !c.is_approved && !c.is_spam).length;
      recentComments.value = all.slice(0, 7);
    }
  } catch { /* ignore */ }
});
</script>
