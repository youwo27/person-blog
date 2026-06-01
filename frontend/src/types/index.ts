// ── API Response ────────────────────────────────
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  results?: T[];
  count?: number;
  next?: string | null;
  previous?: string | null;
  total_pages?: number;
  current_page?: number;
  message?: string;
  error?: { code: string; message: string; details?: any };
}

// ── User ────────────────────────────────────────
export interface UserBrief {
  id: number;
  username: string;
  display_name: string;
  avatar_url: string;
  role: "ADMIN" | "EDITOR" | "AUTHOR" | "USER";
}

export interface UserProfile extends UserBrief {
  email: string;
  first_name: string;
  last_name: string;
  bio: string;
  website: string;
  email_verified: boolean;
  date_joined: string;
  created_at: string;
}

// ── Blog ────────────────────────────────────────
export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  order: number;
  is_active: boolean;
  post_count: number;
  children?: Category[];
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
  post_count: number;
}

export interface Post {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  cover_image_url: string;
  author: UserBrief;
  category: Category | null;
  tags: Tag[];
  status: "DRAFT" | "PUBLISHED" | "ARCHIVED" | "SCHEDULED";
  is_featured: boolean;
  view_count: number;
  reading_time_minutes: number;
  published_at: string | null;
  created_at: string;
}

export interface PostDetail extends Post {
  content: string;
  content_html: string;
  scheduled_at: string | null;
  meta_title: string;
  meta_description: string;
  comment_count: number;
  prev_post: { id: number; title: string; slug: string } | null;
  next_post: { id: number; title: string; slug: string } | null;
  updated_at: string;
}

// ── Comment ─────────────────────────────────────
export interface Comment {
  id: number;
  post: number;
  author: UserBrief;
  parent: number | null;
  content_html: string;
  is_approved: boolean;
  likes_count: number;
  created_at: string;
  replies?: Comment[];
}

// ── Auth ────────────────────────────────────────
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: UserProfile;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
}

// ── Query Params ────────────────────────────────
export interface PostQueryParams {
  page?: number;
  page_size?: number;
  status?: string;
  category?: string;
  tag?: string;
  author?: string;
  featured?: boolean;
  year?: number;
  month?: number;
  search?: string;
  ordering?: string;
}

// ── Site Settings ───────────────────────────────
export interface SiteSettings {
  blog_title: string;
  blog_description: string;
  posts_per_page: number;
  enable_comments: boolean;
  social_github: string;
  social_twitter: string;
  [key: string]: any;
}
