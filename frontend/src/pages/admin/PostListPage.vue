<template>
  <div>
    <!-- Actions Bar -->
    <div class="flex flex-wrap items-center justify-between mb-4 gap-3">
      <div class="flex items-center gap-2">
        <select v-model="filterStatus" @change="fetchPosts" class="px-3 py-2 border rounded-lg text-sm">
          <option value="">全部状态</option>
          <option value="PUBLISHED">已发布</option>
          <option value="DRAFT">草稿</option>
          <option value="ARCHIVED">已归档</option>
          <option value="SCHEDULED">定时发布</option>
        </select>
        <input v-model="search" @keyup.enter="fetchPosts" placeholder="搜索标题..." class="px-3 py-2 border rounded-lg text-sm w-48" />
      </div>
      <router-link to="/admin/posts/new" class="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition flex items-center gap-1.5">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg> 写文章
      </router-link>
    </div>

    <!-- Table -->
    <DataTable :columns="columns" :rows="posts" selectable @selection-change="onSelection">
      <template #cell-title="{ row }">
        <router-link :to="`/admin/posts/${row.slug}/edit`" class="font-medium hover:text-primary-600">{{ row.title }}</router-link>
        <div class="text-xs text-gray-400 mt-0.5">{{ row.slug }}</div>
      </template>
      <template #cell-status="{ row }">
        <span :class="statusBadge(row.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ statusLabel(row.status) }}</span>
      </template>
      <template #cell-author="{ row }">{{ row.author?.display_name }}</template>
      <template #cell-category="{ row }">{{ row.category?.name || '—' }}</template>
      <template #cell-view_count="{ row }">{{ row.view_count?.toLocaleString() }}</template>
      <template #cell-published_at="{ row }">{{ row.published_at ? formatDate(row.published_at) : '—' }}</template>
      <template #cell-actions="{ row }">
        <div class="flex items-center gap-2">
          <router-link :to="`/admin/posts/${row.slug}/edit`" class="text-primary-600 hover:underline text-xs">编辑</router-link>
          <button @click="confirmDelete(row)" class="text-red-600 hover:underline text-xs">删除</button>
        </div>
      </template>
      <template #header>
        <span class="font-semibold text-sm">文章 ({{ total }})</span>
      </template>
      <template #footer>
        <div class="flex justify-between items-center">
          <button v-if="selectedIds.length" @click="confirmBulkDelete" class="text-xs text-red-600 hover:underline">删除选中 ({{ selectedIds.length }})</button>
          <span v-else class="text-xs text-gray-400">共 {{ total }} 篇</span>
          <div class="flex gap-1">
            <button v-for="p in totalPages" :key="p" @click="fetchPosts(p)" :class="['px-3 py-1 text-xs rounded border', page === p ? 'bg-primary-600 text-white border-primary-600' : 'hover:bg-gray-100']">{{ p }}</button>
          </div>
        </div>
      </template>
    </DataTable>

    <ConfirmDialog :visible="deleteDialog.visible" title="删除文章" :message="`确定要删除「${deleteDialog.title}」吗？此操作不可撤销。`" confirm-text="删除" confirm-class="bg-red-600 hover:bg-red-700" @confirm="doDelete" @cancel="deleteDialog.visible=false" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { postsApi } from "@/api";
import type { Post } from "@/types";
import DataTable from "@/components/admin/DataTable.vue";
import ConfirmDialog from "@/components/admin/ConfirmDialog.vue";

const columns = [
  { key: "title", label: "标题" },
  { key: "status", label: "状态", class: "w-20" },
  { key: "author", label: "作者", class: "w-24" },
  { key: "category", label: "分类", class: "w-20" },
  { key: "view_count", label: "浏览", class: "w-20" },
  { key: "published_at", label: "发布时间", class: "w-28" },
  { key: "actions", label: "操作", class: "w-24" },
];

const posts = ref<Post[]>([]);
const page = ref(1);
const total = ref(0);
const totalPages = ref(1);
const filterStatus = ref("");
const search = ref("");
const selectedIds = ref<number[]>([]);
const deleteDialog = ref({ visible: false, title: "", id: 0 });

function statusBadge(s: string) { return s === "PUBLISHED" ? "bg-green-100 text-green-700" : s === "DRAFT" ? "bg-gray-100 text-gray-600" : s === "ARCHIVED" ? "bg-red-100 text-red-600" : "bg-blue-100 text-blue-600"; }
function statusLabel(s: string) { return s === "PUBLISHED" ? "已发布" : s === "DRAFT" ? "草稿" : s === "ARCHIVED" ? "已归档" : "定时"; }
function formatDate(d: string) { return new Date(d).toLocaleDateString("zh-CN"); }
function onSelection(ids: number[]) { selectedIds.value = ids; }

async function fetchPosts(p?: number) {
  if (p) page.value = p;
  try {
    const params: any = { page: page.value, page_size: 15 };
    if (filterStatus.value) params.status = filterStatus.value;
    if (search.value) params.search = search.value;
    const { data } = await postsApi.list(params);
    if (data.success) {
      posts.value = data.results || [];
      total.value = data.count || 0;
      totalPages.value = data.total_pages || 1;
    }
  } catch { /* ignore */ }
}

function confirmDelete(post: Post) { deleteDialog.value = { visible: true, title: post.title, id: post.id }; }
async function doDelete() {
  try {
    const post = posts.value.find((p) => p.id === deleteDialog.value.id);
    if (post) await postsApi.delete(post.slug);
    deleteDialog.value.visible = false;
    fetchPosts();
  } catch { /* ignore */ }
}

async function confirmBulkDelete() {
  for (const id of selectedIds.value) {
    const post = posts.value.find((p) => p.id === id);
    if (post) {
      try { await postsApi.delete(post.slug); } catch { /* ignore */ }
    }
  }
  selectedIds.value = [];
  fetchPosts();
}

onMounted(() => fetchPosts());
</script>
