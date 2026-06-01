import axios from "axios";
import type { AxiosInstance } from "axios";
import type { ApiResponse, Post, PostDetail, Category, Tag, Comment, SiteSettings, LoginRequest, LoginResponse, RegisterRequest, PostQueryParams, UserProfile } from "@/types";

const api: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor — attach JWT ──────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor — unwrap ──────────────
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    // Auto-refresh on 401
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post("/api/v1/auth/refresh/", { refresh });
          localStorage.setItem("access_token", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

// ═══════════════════════════════════════════════════
// Posts API
// ═══════════════════════════════════════════════════
export const postsApi = {
  list(params?: PostQueryParams) {
    return api.get<ApiResponse<Post>>("/posts/", { params });
  },
  get(slug: string) {
    return api.get<ApiResponse<PostDetail>>(`/posts/${slug}/`);
  },
  featured() {
    return api.get<ApiResponse<Post>>("/posts/featured/");
  },
  archive() {
    return api.get<{ success: boolean; results: { month: string; count: number }[] }>("/posts/archive/");
  },
  myPosts(params?: PostQueryParams) {
    return api.get<ApiResponse<Post>>("/posts/my_posts/", { params });
  },
  create(data: Partial<Post>) {
    return api.post<ApiResponse<PostDetail>>("/posts/", data);
  },
  update(slug: string, data: Partial<Post>) {
    return api.patch<ApiResponse<PostDetail>>(`/posts/${slug}/`, data);
  },
  delete(slug: string) {
    return api.delete<ApiResponse<null>>(`/posts/${slug}/`);
  },
};

// ═══════════════════════════════════════════════════
// Categories API
// ═══════════════════════════════════════════════════
export const categoriesApi = {
  list() {
    return api.get<ApiResponse<Category>>("/categories/");
  },
  get(id: number) {
    return api.get<ApiResponse<Category>>(`/categories/${id}/`);
  },
};

// ═══════════════════════════════════════════════════
// Tags API
// ═══════════════════════════════════════════════════
export const tagsApi = {
  list() {
    return api.get<ApiResponse<Tag>>("/tags/");
  },
};

// ═══════════════════════════════════════════════════
// Comments API
// ═══════════════════════════════════════════════════
export const commentsApi = {
  list(postId?: number) {
    return api.get<ApiResponse<Comment>>("/comments/", { params: postId ? { post: postId } : {} });
  },
  create(data: { post_id: number; parent_id?: number; content: string }) {
    return api.post<ApiResponse<Comment>>("/comments/", data);
  },
  like(id: number) {
    return api.post<ApiResponse<{ liked: boolean; likes_count: number }>>(`/comments/${id}/like/`);
  },
};

// ═══════════════════════════════════════════════════
// Auth API
// ═══════════════════════════════════════════════════
export const authApi = {
  login(data: LoginRequest) {
    return api.post<{ success: boolean } & LoginResponse>("/auth/login/", data);
  },
  register(data: RegisterRequest) {
    return api.post<ApiResponse<any>>("/auth/register/", data);
  },
  logout(refresh: string) {
    return api.post("/auth/logout/", { refresh });
  },
  me() {
    return api.get<ApiResponse<UserProfile>>("/auth/me/");
  },
  updateProfile(data: Partial<UserProfile>) {
    return api.patch<ApiResponse<UserProfile>>("/auth/me/", data);
  },
  changePassword(data: { old_password: string; new_password: string; new_password_confirm: string }) {
    return api.patch<ApiResponse<null>>("/auth/change-password/", data);
  },
};

// ═══════════════════════════════════════════════════
// Settings API
// ═══════════════════════════════════════════════════
export const settingsApi = {
  get() {
    return api.get<ApiResponse<SiteSettings>>("/settings/");
  },
};

export default api;
