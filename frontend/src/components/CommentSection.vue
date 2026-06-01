<template>
  <div class="mt-12 border-t pt-8">
    <h3 class="text-xl font-bold mb-6">评论 ({{ totalComments }})</h3>

    <!-- Comment Form -->
    <div v-if="token" class="bg-gray-50 rounded-xl p-4 mb-8">
      <div class="flex gap-3">
        <div class="w-9 h-9 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-semibold shrink-0">
          {{ userInitial }}
        </div>
        <div class="flex-1">
          <textarea
            v-model="newComment"
            :placeholder="replyTo ? '回复 @' + replyTo.author.display_name + '...' : '写下你的评论...'"
            rows="3"
            class="w-full px-4 py-3 border rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-400"
            @keydown.ctrl.enter="submitComment"
          ></textarea>
          <div class="flex items-center justify-between mt-2">
            <span v-if="replyTo" class="text-xs text-gray-500">
              回复 @{{ replyTo.author.display_name }}
              <button @click="replyTo=null" class="text-primary-600 ml-1 hover:underline">取消</button>
            </span>
            <span v-else></span>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-400">Ctrl+Enter 发送</span>
              <button
                @click="submitComment"
                :disabled="!newComment.trim() || submitting"
                class="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50 transition"
              >
                {{ submitting ? '发送中...' : '发表评论' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Login Prompt -->
    <div v-else class="bg-gray-50 rounded-xl p-6 mb-8 text-center">
      <p class="text-gray-500 text-sm">请<router-link to="/login" class="text-primary-600 hover:underline">登录</router-link>后参与评论</p>
    </div>

    <!-- Comment List -->
    <LoadingSpinner v-if="loading" />
    <EmptyState v-else-if="!comments.length" title="暂无评论" description="来说点什么吧" />
    <div v-else class="space-y-0 divide-y">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :depth="0"
        @reply="onReply"
        @like="onLike"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { commentsApi } from "@/api";
import type { Comment } from "@/types";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps<{ postId: number; slug: string }>();

const comments = ref<Comment[]>([]);
const loading = ref(true);
const submitting = ref(false);
const newComment = ref("");
const replyTo = ref<Comment | null>(null);
const token = ref(localStorage.getItem("access_token"));

const totalComments = computed(() => {
  const count = (c: Comment[]): number => c.reduce((s, x) => s + 1 + count(x.replies || []), 0);
  return count(comments.value);
});

const userInitial = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem("user") || "{}");
    return (u.display_name || u.username || "?").charAt(0);
  } catch { return "?"; }
});

async function fetchComments() {
  loading.value = true;
  try {
    const { data } = await commentsApi.list();
    if (data.success && data.results) {
      const all = data.results.filter((c) => (c as any).post === props.postId || (c as any).post_id === props.postId);
      comments.value = all;
    }
  } catch { /* ignore */ }
  loading.value = false;
}

async function submitComment() {
  if (!newComment.value.trim() || submitting.value) return;
  submitting.value = true;
  try {
    const payload: any = { post_id: props.postId, content: newComment.value.trim() };
    if (replyTo.value) payload.parent_id = replyTo.value.id;

    const { data } = await commentsApi.create(payload);
    if (data.success && data.data) {
      if (replyTo.value) {
        if (!replyTo.value.replies) replyTo.value.replies = [];
        replyTo.value.replies.push(data.data);
      } else {
        comments.value.unshift(data.data);
      }
      newComment.value = "";
      replyTo.value = null;
    }
  } catch (err: any) {
    alert(err?.response?.data?.error?.message || "评论失败");
  } finally {
    submitting.value = false;
  }
}

function onReply(comment: Comment) {
  replyTo.value = comment;
}

async function onLike(commentId: number) {
  try {
    const { data } = await commentsApi.like(commentId);
    if (data.success) {
      const update = (list: Comment[]) => {
        for (const c of list) {
          if (c.id === commentId) { c.likes_count = data.data.likes_count; return true; }
          if (c.replies && update(c.replies)) return true;
        }
        return false;
      };
      update(comments.value);
    }
  } catch { /* ignore */ }
}

onMounted(() => fetchComments());
</script>
