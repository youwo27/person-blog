import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0 };
  },
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/pages/HomePage.vue"),
    },
    {
      path: "/posts",
      name: "posts",
      component: () => import("@/pages/PostListPage.vue"),
    },
    {
      path: "/posts/:slug",
      name: "post-detail",
      component: () => import("@/pages/PostDetailPage.vue"),
    },
    {
      path: "/categories/:slug",
      name: "category",
      component: () => import("@/pages/PostListPage.vue"),
      props: (route) => ({ categorySlug: route.params.slug }),
    },
    {
      path: "/tags/:slug",
      name: "tag",
      component: () => import("@/pages/PostListPage.vue"),
      props: (route) => ({ tagSlug: route.params.slug }),
    },
    {
      path: "/search",
      name: "search",
      component: () => import("@/pages/SearchPage.vue"),
    },
    {
      path: "/:pathMatch(.*)*",
      name: "not-found",
      component: () => import("@/pages/NotFoundPage.vue"),
    },
  ],
});

export default router;
