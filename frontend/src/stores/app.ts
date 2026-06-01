import { defineStore } from "pinia";
import { ref } from "vue";
import type { Category, SiteSettings, Tag } from "@/types";
import { categoriesApi, tagsApi, settingsApi } from "@/api";

export const useAppStore = defineStore("app", () => {
  const settings = ref<SiteSettings>({ blog_title: "Person Blog", blog_description: "", posts_per_page: 12, enable_comments: true, social_github: "", social_twitter: "" });
  const categories = ref<Category[]>([]);
  const tags = ref<Tag[]>([]);
  const loading = ref(false);
  const searchQuery = ref("");
  const theme = ref<"light" | "dark">("light");

  async function fetchSettings() {
    try {
      const { data } = await settingsApi.get();
      if (data.success && data.results) Object.assign(settings.value, data.results);
    } catch { /* use defaults */ }
  }

  async function fetchCategories() {
    try {
      const { data } = await categoriesApi.list();
      if (data.success && data.results) categories.value = data.results;
    } catch { /* empty */ }
  }

  async function fetchTags() {
    try {
      const { data } = await tagsApi.list();
      if (data.success && data.results) tags.value = data.results;
    } catch { /* empty */ }
  }

  async function init() {
    loading.value = true;
    await Promise.all([fetchSettings(), fetchCategories(), fetchTags()]);
    loading.value = false;
  }

  function setSearch(q: string) { searchQuery.value = q; }
  function toggleTheme() {
    theme.value = theme.value === "light" ? "dark" : "light";
    document.documentElement.classList.toggle("dark", theme.value === "dark");
  }

  return { settings, categories, tags, loading, searchQuery, theme, init, setSearch, toggleTheme };
});
