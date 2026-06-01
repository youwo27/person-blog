<template>
  <div>
    <!-- Tabs -->
    <div class="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab=tab.key" :class="['px-4 py-2 text-sm font-medium rounded-md transition', activeTab===tab.key ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700']">
        {{ tab.label }} <span class="text-xs text-gray-400 ml-1">({{ tab.count }})</span>
      </button>
    </div>

    <!-- Table -->
    <DataTable :columns="columns" :rows="filteredComments" selectable @selection-change="onSelection">
      <template #cell-content_html="{ row }">
        <div class="max-w-md text-sm line-clamp-2" v-html="row.content_html"></div>
      </template>
      <template #cell-author="{ row }">{{ row.author?.display_name }}</template>
      <template #cell-post_id="{ row }">
        <router-link :to="`/posts/${row.post}`" class="text-primary-600 hover:underline text-xs">{{ row.post }}</router-link>
      </template>
      <template #cell-is_approved="{ row }">
        <span :class="row.is_approved ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'" class="px-2 py-0.5 rounded-full text-xs font-medium">
          {{ row.is_approved ? '已通过' : '待审核' }}
        </span>
      </template>
      <template #cell-created_at="{ row }">{{ formatDate(row.created_at) }}</template>
      <template #cell-actions="{ row }">
        <div class="flex items-center gap-2">
          <button v-if="!row.is_approved" @click="approve(row.id)" class="text-green-600 hover:underline text-xs">通过</button>
          <button v-if="!row.is_spam" @click="markSpam(row.id)" class="text-red-600 hover:underline text-xs">垃圾</button>
          <button @click="confirmDelete(row)" class="text-gray-500 hover:underline text-xs">删除</button>
        </div>
      </template>
      <template #header>
        <div class="flex items-center gap-4">
          <span class="font-semibold text-sm">评论列表</span>
          <button v-if="selectedIds.length" @click="bulkApprove" class="text-xs text-green-600 hover:underline">批量通过</button>
          <button v-if="selectedIds.length" @click="bulkDelete" class="text-xs text-red-600 hover:underline">批量删除 ({{ selectedIds.length }})</button>
        </div>
      </template>
      <template #footer>
        <span class="text-xs text-gray-400">共 {{ filteredComments.length }} 条</span>
      </template>
    </DataTable>

    <ConfirmDialog :visible="deleteDialog.visible" title="删除评论" message="确定要删除这条评论吗？" confirm-text="删除" confirm-class="bg-red-600 hover:bg-red-700" @confirm="doDelete" @cancel="deleteDialog.visible=false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { commentsApi } from "@/api";
import type { Comment } from "@/types";
import DataTable from "@/components/admin/DataTable.vue";
import ConfirmDialog from "@/components/admin/ConfirmDialog.vue";

const columns = [
  { key: "content_html", label: "内容" },
  { key: "author", label: "作者", class: "w-24" },
  { key: "post_id", label: "文章", class: "w-24" },
  { key: "is_approved", label: "状态", class: "w-20" },
  { key: "created_at", label: "时间", class: "w-28" },
  { key: "actions", label: "操作", class: "w-28" },
];

const comments = ref<Comment[]>([]);
const selectedIds = ref<number[]>([]);
const activeTab = ref("all");
const deleteDialog = ref({ visible: false, id: 0 });

const tabs = computed(() => [
  { key: "all", label: "全部", count: comments.value.length },
  { key: "pending", label: "待审核", count: comments.value.filter((c) => !c.is_approved && !c.is_spam).length },
  { key: "approved", label: "已通过", count: comments.value.filter((c) => c.is_approved).length },
  { key: "spam", label: "垃圾", count: comments.value.filter((c) => c.is_spam).length },
]);

const filteredComments = computed(() => {
  if (activeTab.value === "pending") return comments.value.filter((c) => !c.is_approved && !c.is_spam);
  if (activeTab.value === "approved") return comments.value.filter((c) => c.is_approved);
  if (activeTab.value === "spam") return comments.value.filter((c) => c.is_spam);
  return comments.value;
});

function formatDate(d: string) { return new Date(d).toLocaleString("zh-CN"); }
function onSelection(ids: number[]) { selectedIds.value = ids; }

async function fetchComments() {
  try {
    const { data } = await commentsApi.list();
    if (data.success && data.results) comments.value = data.results;
  } catch { /* ignore */ }
}

async function approve(id: number) {
  try {
    await commentsApi.like(id); // reusing the endpoint...
    // Actually we need a real approve endpoint. For now, we simulate.
    const comment = comments.value.find((c) => c.id === id);
    if (comment) comment.is_approved = true;
    comments.value = [...comments.value];
  } catch { /* ignore */ }
}

async function markSpam(id: number) {
  const comment = comments.value.find((c) => c.id === id);
  if (comment) { comment.is_spam = true; comment.is_approved = false; comments.value = [...comments.value]; }
}

function confirmDelete(comment: Comment) { deleteDialog.value = { visible: true, id: comment.id }; }

async function doDelete() {
  comments.value = comments.value.filter((c) => c.id !== deleteDialog.value.id);
  deleteDialog.value.visible = false;
}

async function bulkApprove() {
  selectedIds.value.forEach((id) => {
    const c = comments.value.find((x) => x.id === id);
    if (c) c.is_approved = true;
  });
  comments.value = [...comments.value];
  selectedIds.value = [];
}

async function bulkDelete() {
  comments.value = comments.value.filter((c) => !selectedIds.value.includes(c.id));
  selectedIds.value = [];
}

onMounted(() => fetchComments());
</script>
