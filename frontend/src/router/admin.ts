import type { RouteRecordRaw } from "vue-router";
import AdminLayout from "@/layouts/AdminLayout.vue";

const adminRoutes: RouteRecordRaw[] = [
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true, requiresRole: ["AUTHOR", "EDITOR", "ADMIN"] },
    children: [
      {
        path: "",
        name: "admin-dashboard",
        component: () => import("@/pages/admin/DashboardPage.vue"),
        meta: { title: "仪表盘" },
      },
      {
        path: "posts",
        name: "admin-posts",
        component: () => import("@/pages/admin/PostListPage.vue"),
        meta: { title: "文章管理" },
      },
      {
        path: "posts/new",
        name: "admin-post-new",
        component: () => import("@/pages/admin/PostEditorPage.vue"),
        meta: { title: "写文章" },
      },
      {
        path: "posts/:slug/edit",
        name: "admin-post-edit",
        component: () => import("@/pages/admin/PostEditorPage.vue"),
        meta: { title: "编辑文章" },
        props: true,
      },
      {
        path: "comments",
        name: "admin-comments",
        component: () => import("@/pages/admin/CommentPage.vue"),
        meta: { title: "评论审核" },
      },
      {
        path: "media",
        name: "admin-media",
        component: () => import("@/pages/admin/MediaPage.vue"),
        meta: { title: "媒体库" },
      },
    ],
  },
];

export default adminRoutes;
