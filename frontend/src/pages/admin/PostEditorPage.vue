<template>
  <div class="max-w-6xl">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Editor -->
      <div class="lg:col-span-3 space-y-4">
        <!-- Title -->
        <div>
          <input v-model="form.title" placeholder="文章标题" class="w-full text-3xl font-bold border-0 border-b-2 border-gray-200 focus:border-primary-500 py-2 px-0 outline-none placeholder:text-gray-300" />
        </div>

        <!-- Slug -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400">/posts/</span>
          <input v-model="form.slug" placeholder="article-slug" class="flex-1 text-sm border rounded px-2 py-1 outline-none focus:border-primary-400" />
          <button @click="generateSlug" class="text-xs text-primary-600 hover:underline">自动生成</button>
        </div>

        <!-- Markdown Editor -->
        <div class="border rounded-xl overflow-hidden">
          <div class="flex border-b bg-gray-50">
            <button @click="tab='write'" :class="['flex-1 py-2.5 text-sm font-medium text-center transition', tab==='write' ? 'bg-white text-gray-900 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-700']">编辑</button>
            <button @click="tab='preview'" :class="['flex-1 py-2.5 text-sm font-medium text-center transition', tab==='preview' ? 'bg-white text-gray-900 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-700']">预览</button>
          </div>
          <div v-show="tab==='write'" class="p-0">
            <textarea v-model="form.content" placeholder="使用 Markdown 编写文章内容..." class="w-full h-[500px] p-6 outline-none resize-none font-mono text-sm leading-relaxed"></textarea>
          </div>
          <div v-show="tab==='preview'" class="p-6 min-h-[500px] post-content prose max-w-none" v-html="renderedPreview"></div>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between">
          <div class="flex gap-2">
            <button @click="save('DRAFT')" class="px-5 py-2 border rounded-lg text-sm hover:bg-gray-50 transition" :disabled="saving">
              {{ saving ? '保存中...' : '存草稿' }}
            </button>
            <button @click="save('PUBLISHED')" class="px-5 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition disabled:opacity-50" :disabled="saving">
              {{ saving ? '发布中...' : '发布' }}
            </button>
          </div>
          <span v-if="savedMsg" class="text-sm text-green-600">{{ savedMsg }}</span>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="lg:col-span-1 space-y-4">
        <!-- Status -->
        <div class="bg-white rounded-xl border p-4">
          <h4 class="text-sm font-semibold mb-3 text-gray-700">发布状态</h4>
          <select v-model="form.status" class="w-full px-3 py-2 border rounded-lg text-sm">
            <option value="DRAFT">草稿</option>
            <option value="PUBLISHED">发布</option>
            <option value="ARCHIVED">归档</option>
            <option value="SCHEDULED">定时发布</option>
          </select>
          <div v-if="form.status === 'SCHEDULED'" class="mt-2">
            <input type="datetime-local" v-model="form.scheduled_at" class="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
        </div>

        <!-- Featured -->
        <div class="bg-white rounded-xl border p-4">
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="form.is_featured" class="w-4 h-4 rounded text-primary-600" />
            <span class="text-sm font-medium text-gray-700">精选文章</span>
          </label>
        </div>

        <!-- Category -->
        <div class="bg-white rounded-xl border p-4">
          <h4 class="text-sm font-semibold mb-3 text-gray-700">分类</h4>
          <select v-model="form.category_id" class="w-full px-3 py-2 border rounded-lg text-sm">
            <option :value="null">无分类</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </div>

        <!-- Tags -->
        <div class="bg-white rounded-xl border p-4">
          <h4 class="text-sm font-semibold mb-3 text-gray-700">标签</h4>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="tag in tags"
              :key="tag.id"
              @click="toggleTag(tag.id)"
              :class="['px-2.5 py-1 rounded-full text-xs border transition', selectedTagIds.includes(tag.id) ? 'bg-primary-600 text-white border-primary-600' : 'hover:border-primary-400']"
            >
              {{ tag.name }}
            </button>
          </div>
        </div>

        <!-- Cover Image -->
        <div class="bg-white rounded-xl border p-4">
          <h4 class="text-sm font-semibold mb-3 text-gray-700">封面图片</h4>
          <input v-model="form.cover_image_id" type="number" placeholder="输入 Media ID" class="w-full px-3 py-2 border rounded-lg text-xs" />
          <p class="text-xs text-gray-400 mt-1">从媒体库获取 ID，或留空</p>
        </div>

        <!-- SEO -->
        <div class="bg-white rounded-xl border p-4">
          <h4 class="text-sm font-semibold mb-3 text-gray-700">SEO 设置</h4>
          <label class="text-xs text-gray-500">Meta Title</label>
          <input v-model="form.meta_title" :placeholder="form.title" class="w-full px-3 py-2 border rounded-lg text-sm mb-2 mt-1" />
          <label class="text-xs text-gray-500">Meta Description</label>
          <textarea v-model="form.meta_description" rows="2" class="w-full px-3 py-2 border rounded-lg text-sm mt-1" placeholder="文章摘要..."></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { postsApi } from "@/api";
import { useAppStore } from "@/stores/app";

const route = useRoute();
const router = useRouter();
const store = useAppStore();
const { categories, tags } = store;

const tab = ref<"write" | "preview">("write");
const saving = ref(false);
const savedMsg = ref("");
const selectedTagIds = ref<number[]>([]);
const isEdit = ref(false);
const editSlug = ref("");
const form = ref({
  title: "", slug: "", content: "", excerpt: "",
  status: "DRAFT" as string, is_featured: false,
  category_id: null as number | null,
  scheduled_at: "",
  cover_image_id: null as number | null,
  meta_title: "", meta_description: "",
});

const renderedPreview = computed(() => {
  if (!form.value.content) return '<p class="text-gray-400">暂无内容</p>';
  try {
    // Simple markdown-like rendering for preview
    let html = form.value.content
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
    return `<p>${html}</p>`;
  } catch { return form.value.content; }
});

function generateSlug() {
  if (!form.value.title) return;
  form.value.slug = form.value.title
    .toLowerCase()
    .replace(/[^\w一-鿿]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 100) || `post-${Date.now()}`;
}

function toggleTag(id: number) {
  const idx = selectedTagIds.value.indexOf(id);
  if (idx >= 0) selectedTagIds.value.splice(idx, 1);
  else selectedTagIds.value.push(id);
}

async function save(status: string) {
  saving.value = true;
  savedMsg.value = "";
  form.value.status = status;

  const payload: any = {
    title: form.value.title,
    slug: form.value.slug || undefined,
    content: form.value.content,
    excerpt: form.value.excerpt || undefined,
    status: form.value.status,
    is_featured: form.value.is_featured,
    category_id: form.value.category_id || null,
    tag_ids: selectedTagIds.value.length ? selectedTagIds.value : undefined,
    cover_image_id: form.value.cover_image_id || null,
    scheduled_at: form.value.scheduled_at || undefined,
    meta_title: form.value.meta_title || undefined,
    meta_description: form.value.meta_description || undefined,
  };

  try {
    if (isEdit.value) {
      await postsApi.update(editSlug.value, payload);
    } else {
      const { data } = await postsApi.create(payload);
      if (data.success && data.data) {
        isEdit.value = true;
        editSlug.value = data.data.slug;
        router.replace(`/admin/posts/${data.data.slug}/edit`);
      }
    }
    savedMsg.value = status === "PUBLISHED" ? "发布成功!" : "已保存";
    setTimeout(() => (savedMsg.value = ""), 3000);
  } catch (err: any) {
    savedMsg.value = "保存失败";
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  await Promise.all([store.fetchCategories(), store.fetchTags()]);

  const slug = route.params.slug as string;
  if (slug) {
    isEdit.value = true;
    editSlug.value = slug;
    try {
      const { data } = await postsApi.get(slug);
      if (data.success && data.data) {
        const p = data.data;
        form.value = {
          title: p.title, slug: p.slug, content: p.content,
          excerpt: p.excerpt, status: p.status, is_featured: p.is_featured,
          category_id: p.category?.id || null,
          scheduled_at: p.scheduled_at ? p.scheduled_at.slice(0, 16) : "",
          cover_image_id: null as any,
          meta_title: p.meta_title, meta_description: p.meta_description,
        };
        selectedTagIds.value = p.tags?.map((t) => t.id) || [];
      }
    } catch { /* ignore */ }
  }
});
</script>
