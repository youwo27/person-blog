import { createRouter, createWebHistory } from "vue-router";
import adminRoutes from "./admin";

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() { return { top: 0 }; },
  routes: [
    ...adminRoutes,
    { path: "/", name: "home", component: () => import("@/pages/HomePage.vue") },
    { path: "/posts", name: "posts", component: () => import("@/pages/PostListPage.vue") },
    { path: "/posts/:slug", name: "post-detail", component: () => import("@/pages/PostDetailPage.vue") },
    { path: "/categories/:slug", name: "category", component: () => import("@/pages/PostListPage.vue"), props: (r) => ({ categorySlug: r.params.slug }) },
    { path: "/tags/:slug", name: "tag", component: () => import("@/pages/PostListPage.vue"), props: (r) => ({ tagSlug: r.params.slug }) },
    { path: "/search", name: "search", component: () => import("@/pages/SearchPage.vue") },
    { path: "/:pathMatch(.*)*", name: "not-found", component: () => import("@/pages/NotFoundPage.vue") },
  ],
});

// ── Auth guard ──────────────────────────────────
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth);
  if (!requiresAuth) return next();

  const token = localStorage.getItem("access_token");
  if (!token) return next("/");

  const requiredRole = to.meta.requiresRole as string[] | undefined;
  if (requiredRole) {
    try {
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      if (!requiredRole.includes(user.role)) return next("/admin");
    } catch {
      return next("/");
    }
  }
  next();
});

export default router;
