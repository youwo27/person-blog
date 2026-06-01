<template>
  <div>
    <!-- Upload Bar -->
    <div class="bg-white rounded-xl border p-4 mb-6">
      <div class="flex items-center gap-4">
        <label class="flex-1">
          <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary-400 hover:bg-primary-50/30 transition">
            <svg class="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
            <span class="text-sm text-gray-500">拖拽文件到此处，或点击上传</span>
            <span class="text-xs text-gray-400 block mt-1">支持 JPG, PNG, GIF, WebP, PDF · 最大 10MB</span>
          </div>
          <input type="file" accept="image/*,.pdf" @change="handleUpload" class="hidden" ref="fileInput" multiple />
        </label>
      </div>
      <!-- Upload Progress -->
      <div v-if="uploading" class="mt-3">
        <div class="flex items-center gap-3 text-sm text-gray-600">
          <div class="w-5 h-5 border-2 border-primary-400 border-t-transparent rounded-full animate-spin"></div>
          正在上传...
        </div>
      </div>
      <div v-if="uploadMsg" :class="['mt-3 text-sm', uploadMsgType === 'success' ? 'text-green-600' : 'text-red-600']">{{ uploadMsg }}</div>
    </div>

    <!-- Filter -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex gap-2">
        <button @click="filterType=''" :class="['px-3 py-1.5 rounded-lg text-xs border transition', !filterType ? 'bg-primary-600 text-white border-primary-600' : 'hover:bg-gray-100']">全部</button>
        <button @click="filterType='image/'" :class="['px-3 py-1.5 rounded-lg text-xs border transition', filterType==='image/' ? 'bg-primary-600 text-white border-primary-600' : 'hover:bg-gray-100']">图片</button>
      </div>
      <span class="text-xs text-gray-500">{{ filteredMedia.length }} 个文件</span>
    </div>

    <!-- Grid -->
    <div v-if="filteredMedia.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <div v-for="m in filteredMedia" :key="m.id" class="bg-white rounded-xl border overflow-hidden group hover:shadow-md transition">
        <!-- Preview -->
        <div class="aspect-square bg-gray-100 flex items-center justify-center overflow-hidden relative">
          <img v-if="m.is_image && m.url" :src="m.url" :alt="m.alt_text || m.filename" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" />
          <div v-else class="text-gray-400 text-xs text-center p-2">{{ m.mime_type }}</div>
          <!-- Overlay actions -->
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
            <button @click="copyUrl(m.url)" class="w-8 h-8 bg-white/90 rounded-full flex items-center justify-center hover:bg-white transition" title="复制 URL">
              <svg class="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
            </button>
            <button @click="confirmDelete(m)" class="w-8 h-8 bg-white/90 rounded-full flex items-center justify-center hover:bg-red-50 transition" title="删除">
              <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
        <!-- Info -->
        <div class="p-2.5">
          <div class="text-xs font-medium truncate" :title="m.filename">{{ m.filename }}</div>
          <div class="text-xs text-gray-400 mt-0.5">{{ m.file_size_display }} · {{ formatDate(m.created_at) }}</div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-20 text-gray-400">
      <svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      <p class="text-sm">媒体库为空</p>
      <p class="text-xs mt-1">上传图片或文件开始使用</p>
    </div>

    <ConfirmDialog :visible="deleteDialog.visible" title="删除文件" :message="`确定要删除「${deleteDialog.name}」吗？`" confirm-text="删除" confirm-class="bg-red-600 hover:bg-red-700" @confirm="doDelete" @cancel="deleteDialog.visible=false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import ConfirmDialog from "@/components/admin/ConfirmDialog.vue";

interface MediaItem {
  id: number;
  url: string;
  filename: string;
  mime_type: string;
  file_size_display: string;
  is_image: boolean;
  alt_text: string;
  created_at: string;
}

const media = ref<MediaItem[]>([]);
const filterType = ref("");
const uploading = ref(false);
const uploadMsg = ref("");
const uploadMsgType = ref<"success" | "error">("success");
const fileInput = ref<HTMLInputElement>();
const deleteDialog = ref({ visible: false, name: "", id: 0 });

const filteredMedia = computed(() => {
  if (!filterType.value) return media.value;
  return media.value.filter((m) => m.mime_type.startsWith(filterType.value));
});

function formatDate(d: string) { return new Date(d).toLocaleDateString("zh-CN"); }

async function fetchMedia() {
  try {
    const { data } = await axios.get("/api/v1/media/");
    if (data.success && data.results) media.value = data.results;
  } catch { /* ignore */ }
}

async function handleUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (!files?.length) return;

  uploading.value = true;
  uploadMsg.value = "";
  let success = 0;
  let fail = 0;

  for (const file of Array.from(files)) {
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("alt_text", file.name);
      const token = localStorage.getItem("access_token");
      await axios.post("/api/v1/media/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data", Authorization: token ? `Bearer ${token}` : "" },
      });
      success++;
    } catch {
      fail++;
    }
  }

  uploading.value = false;
  uploadMsgType.value = fail === 0 ? "success" : "error";
  uploadMsg.value = `上传完成：${success} 个成功${fail ? `，${fail} 个失败` : ""}`;
  if (fileInput.value) fileInput.value.value = "";
  fetchMedia();
  setTimeout(() => (uploadMsg.value = ""), 5000);
}

function copyUrl(url: string) {
  if (url) {
    navigator.clipboard.writeText(url.startsWith("http") ? url : window.location.origin + url);
    uploadMsg.value = "URL 已复制";
    uploadMsgType.value = "success";
    setTimeout(() => (uploadMsg.value = ""), 2000);
  }
}

function confirmDelete(m: MediaItem) { deleteDialog.value = { visible: true, name: m.filename, id: m.id }; }

async function doDelete() {
  try {
    const token = localStorage.getItem("access_token");
    await axios.delete(`/api/v1/media/${deleteDialog.value.id}/`, {
      headers: { Authorization: token ? `Bearer ${token}` : "" },
    });
    media.value = media.value.filter((m) => m.id !== deleteDialog.value.id);
  } catch { /* ignore */ }
  deleteDialog.value.visible = false;
}

onMounted(() => fetchMedia());
</script>
