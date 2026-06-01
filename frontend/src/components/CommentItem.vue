<template>
  <div :class="['py-4', depth > 0 ? 'ml-6 pl-4 border-l-2 border-gray-100' : '']">
    <!-- Header -->
    <div class="flex items-center gap-2 mb-2">
      <div class="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600">
        {{ comment.author?.display_name?.charAt(0) || '?' }}
      </div>
      <span class="text-sm font-medium text-gray-900">{{ comment.author?.display_name }}</span>
      <span class="text-xs text-gray-400">{{ formatDate(comment.created_at) }}</span>
    </div>

    <!-- Content -->
    <div class="text-sm text-gray-700 leading-relaxed ml-9" v-html="comment.content_html"></div>

    <!-- Actions -->
    <div class="flex items-center gap-4 mt-2 ml-9">
      <button @click="$emit('like', comment.id)" class="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600 transition">
        <svg class="w-4 h-4" :class="{'text-primary-500': comment.likes_count > 0}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"/>
        </svg>
        {{ comment.likes_count || '' }}
      </button>
      <button
        v-if="depth < 3"
        @click="$emit('reply', comment)"
        class="text-xs text-gray-500 hover:text-primary-600 transition"
      >
        回复
      </button>
    </div>

    <!-- Nested Replies -->
    <div v-if="comment.replies?.length">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :depth="depth + 1"
        @reply="$emit('reply', $event)"
        @like="$emit('like', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Comment } from "@/types";

defineProps<{ comment: Comment; depth: number }>();
defineEmits<{ reply: [comment: Comment]; like: [commentId: number] }>();

function formatDate(d: string) {
  const date = new Date(d);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} 天前`;
  return date.toLocaleDateString("zh-CN");
}
</script>
