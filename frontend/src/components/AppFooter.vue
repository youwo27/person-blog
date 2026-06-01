<template>
  <footer class="bg-gray-900 text-gray-400 mt-16">
    <div class="max-w-7xl mx-auto px-4 py-12 grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- Brand -->
      <div>
        <h3 class="text-white text-lg font-semibold mb-3">{{ store.settings.blog_title }}</h3>
        <p class="text-sm leading-relaxed">{{ store.settings.blog_description }}</p>
      </div>
      <!-- Links -->
      <div>
        <h4 class="text-white text-sm font-semibold mb-3 uppercase tracking-wider">快速链接</h4>
        <ul class="space-y-2 text-sm">
          <li><router-link to="/" class="hover:text-white transition-colors">首页</router-link></li>
          <li><router-link to="/posts" class="hover:text-white transition-colors">全部文章</router-link></li>
          <li v-for="cat in store.categories.slice(0, 5)" :key="cat.id">
            <router-link :to="`/categories/${cat.slug}`" class="hover:text-white transition-colors">{{ cat.name }}</router-link>
          </li>
        </ul>
      </div>
      <!-- Tags -->
      <div>
        <h4 class="text-white text-sm font-semibold mb-3 uppercase tracking-wider">热门标签</h4>
        <div class="flex flex-wrap gap-2">
          <router-link
            v-for="tag in store.tags.slice(0, 10)"
            :key="tag.id"
            :to="`/tags/${tag.slug}`"
            class="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-full text-xs text-gray-300 hover:text-white transition-colors"
          >
            {{ tag.name }}
          </router-link>
        </div>
      </div>
    </div>
    <div class="border-t border-gray-800 py-6 text-center text-xs">
      <p>&copy; {{ new Date().getFullYear() }} {{ store.settings.blog_title }}. Powered by Django + Vue.</p>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { useAppStore } from "@/stores/app";
const store = useAppStore();
</script>
