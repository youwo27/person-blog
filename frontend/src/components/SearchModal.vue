<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" @click.self="close">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 overflow-hidden">
        <!-- Input -->
        <div class="flex items-center gap-3 px-5 py-4 border-b">
          <svg class="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input
            ref="inputEl"
            v-model="query"
            @keydown.esc="close"
            @keydown.enter="doSearch"
            @input="onInput"
            placeholder="搜索文章..."
            class="flex-1 text-lg outline-none placeholder:text-gray-300"
            autofocus
          />
          <kbd class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded hidden sm:inline">ESC</kbd>
        </div>

        <!-- Suggestions -->
        <div v-if="suggestions.length" class="py-2">
          <div v-for="item in suggestions" :key="item.id" @click="goTo(item.slug)" class="flex items-center gap-3 px-5 py-2.5 hover:bg-gray-50 cursor-pointer transition">
            <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            <span class="text-sm">{{ item.title }}</span>
          </div>
        </div>

        <!-- Trending -->
        <div v-if="!query && trending.length" class="py-2">
          <div class="px-5 py-2 text-xs text-gray-400 font-medium">热门搜索</div>
          <div v-for="item in trending" :key="item.term" @click="query=item.term; doSearch()" class="flex items-center justify-between px-5 py-2 hover:bg-gray-50 cursor-pointer transition">
            <span class="text-sm">{{ item.term }}</span>
            <span class="text-xs text-gray-400">{{ item.count }}</span>
          </div>
        </div>

        <!-- Empty -->
        <div v-if="query && !suggestions.length && searchedOnce" class="px-5 py-8 text-center text-sm text-gray-400">
          未找到匹配结果 — 按 Enter 搜索全文
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();
const visible = ref(false);
const query = ref("");
const suggestions = ref<{ id: number; title: string; slug: string }[]>([]);
const trending = ref<{ term: string; count: number }[]>([]);
const searchedOnce = ref(false);
const inputEl = ref<HTMLInputElement>();
let debounceTimer: any;

async function fetchSuggestions(q: string) {
  if (!q.trim()) { suggestions.value = []; return; }
  try {
    const { data } = await axios.get("/api/v1/search/suggest/", { params: { q: q.trim() } });
    if (data.success) suggestions.value = data.results || [];
  } catch { suggestions.value = []; }
}

async function fetchTrending() {
  try {
    const { data } = await axios.get("/api/v1/search/trending/");
    if (data.success) trending.value = data.results || [];
  } catch { /* ignore */ }
}

function onInput() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => fetchSuggestions(query.value), 200);
}

function doSearch() {
  if (!query.value.trim()) return;
  searchedOnce.value = true;
  router.push({ name: "search", query: { q: query.value.trim() } });
  close();
}

function goTo(slug: string) {
  router.push(`/posts/${slug}`);
  close();
}

function open() { visible.value = true; fetchTrending(); nextTick(() => inputEl.value?.focus()); }
function close() { visible.value = false; query.value = ""; suggestions.value = []; searchedOnce.value = false; }

function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); visible.value ? close() : open(); }
}

// Expose for external use
defineExpose({ open, close });

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>
