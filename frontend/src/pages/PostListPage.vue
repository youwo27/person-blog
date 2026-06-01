<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <Breadcrumb :items="breadcrumbItems" />

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
      <!-- Sidebar Filters -->
      <aside class="lg:col-span-1 order-2 lg:order-1">
        <div class="bg-white rounded-xl border p-5 sticky top-24 space-y-6">
          <!-- Search -->
          <div>
            <h4 class="font-semibold text-sm mb-2 text-gray-700">搜索</h4>
            <input
              v-model="filters.search"
              @keyup.enter="applySearch"
              placeholder="搜索文章..."
              class="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          <!-- Status -->
          <div>
            <h4 class="font-semibold text-sm mb-2 text-gray-700">状态</h4>
            <select v-model="filters.status" @change="fetchPosts(1)" class="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
              <option value="">全部</option>
              <option value="PUBLISHED">已发布</option>
              <option value="DRAFT">草稿</option>
            </select>
          </div>

          <!-- Category -->
          <div>
            <h4 class="font-semibold text-sm mb-2 text-gray-700">分类</h4>
            <div class="space-y-1 max-h-48 overflow-y-auto">
              <label
                v-for="cat in store.categories"
                :key="cat.id"
                class="flex items-center gap-2 text-sm cursor-pointer hover:text-primary-600"
              >
                <input
                  type="radio"
                  name="category"
                  :value="cat.slug"
                  v-model="filters.category"
                  @change="fetchPosts(1)"
                  class="text-primary-600"
                />
                {{ cat.name }}
                <span class="text-xs text-gray-400 ml-auto">({{ cat.post_count }})</span>
              </label>
            </div>
          </div>

          <!-- Tags -->
          <div>
            <h4 class="font-semibold text-sm mb-2 text-gray-700">标签</h4>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="tag in store.tags.slice(0, 12)"
                :key="tag.id"
                @click="filters.tag = filters.tag === tag.slug ? '' : tag.slug; fetchPosts(1)"
                :class="[
                  'px-2.5 py-1 rounded-full text-xs border transition',
                  filters.tag === tag.slug
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'hover:border-primary-400 hover:text-primary-600',
                ]"
              >
                {{ tag.name }}
              </button>
            </div>
          </div>

          <!-- Ordering -->
          <div>
            <h4 class="font-semibold text-sm mb-2 text-gray-700">排序</h4>
            <select v-model="filters.ordering" @change="fetchPosts(1)" class="w-full px-3 py-2 border rounded-lg text-sm">
              <option value="-published_at">最新发布</option>
              <option value="-view_count">最多浏览</option>
              <option value="-created_at">最近创建</option>
              <option value="published_at">最早发布</option>
            </select>
          </div>

          <!-- Clear -->
          <button
            @click="clearFilters"
            class="w-full py-2 text-sm text-gray-500 hover:text-gray-700 border rounded-lg hover:bg-gray-50 transition"
          >
            清除筛选
          </button>
        </div>
      </aside>

      <!-- Post Grid -->
      <div class="lg:col-span-3 order-1 lg:order-2">
        <h1 class="text-2xl font-bold mb-6">{{ pageTitle }}</h1>
        <LoadingSpinner v-if="loading" />
        <EmptyState v-else-if="!posts.length" title="没有找到文章" description="换个筛选条件试试" />
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <PostCard v-for="post in posts" :key="post.id" :post="post" />
        </div>
        <Pagination
          :current-page="currentPage"
          :total-pages="totalPages"
          :total="total"
          @page-change="fetchPosts"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { postsApi } from "@/api";
import { useAppStore } from "@/stores/app";
import type { Post } from "@/types";
import PostCard from "@/components/PostCard.vue";
import Pagination from "@/components/Pagination.vue";
import Breadcrumb from "@/components/Breadcrumb.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps<{ categorySlug?: string; tagSlug?: string }>();
const route = useRoute();
const store = useAppStore();

const posts = ref<Post[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);
const total = ref(0);

const filters = ref({
  search: (route.query.search as string) || "",
  status: (route.query.status as string) || "",
  category: props.categorySlug || (route.query.category as string) || "",
  tag: props.tagSlug || (route.query.tag as string) || "",
  featured: route.query.featured === "true" ? true : undefined as boolean | undefined,
  ordering: (route.query.ordering as string) || "-published_at",
});

const pageTitle = computed(() => {
  if (props.categorySlug) {
    const cat = store.categories.find((c) => c.slug === props.categorySlug);
    return cat ? `分类：${cat.name}` : "分类文章";
  }
  if (props.tagSlug) {
    const tag = store.tags.find((t) => t.slug === props.tagSlug);
    return tag ? `标签：${tag.name}` : "标签文章";
  }
  return "全部文章";
});

const breadcrumbItems = computed(() => {
  const items: { label: string; to?: string }[] = [];
  if (props.categorySlug) {
    items.push({ label: "全部文章", to: "/posts" });
    const cat = store.categories.find((c) => c.slug === props.categorySlug);
    items.push({ label: cat?.name || props.categorySlug });
  } else if (props.tagSlug) {
    items.push({ label: "全部文章", to: "/posts" });
    const tag = store.tags.find((t) => t.slug === props.tagSlug);
    items.push({ label: tag?.name || props.tagSlug });
  } else {
    items.push({ label: "全部文章" });
  }
  return items;
});

async function fetchPosts(page: number = 1) {
  loading.value = true;
  currentPage.value = page;
  try {
    const params: any = { page, page_size: 12 };
    if (filters.value.search) params.search = filters.value.search;
    if (filters.value.status) params.status = filters.value.status;
    if (filters.value.category) params.category = filters.value.category;
    if (filters.value.tag) params.tag = filters.value.tag;
    if (filters.value.featured !== undefined) params.featured = filters.value.featured;
    if (filters.value.ordering) params.ordering = filters.value.ordering;

    const { data } = await postsApi.list(params);
    if (data.success) {
      posts.value = data.results || [];
      total.value = data.count || 0;
      totalPages.value = data.total_pages || 1;
    }
  } catch {
    /* ignore */
  } finally {
    loading.value = false;
  }
}

function applySearch() {
  fetchPosts(1);
}

function clearFilters() {
  filters.value = { search: "", status: "", category: "", tag: "", featured: undefined, ordering: "-published_at" };
  fetchPosts(1);
}

watch(() => props.categorySlug, (val) => {
  if (val) { filters.value.category = val; fetchPosts(1); }
});
watch(() => props.tagSlug, (val) => {
  if (val) { filters.value.tag = val; fetchPosts(1); }
});

onMounted(() => fetchPosts());
</script>
