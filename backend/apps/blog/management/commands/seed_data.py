"""
Seed data management command.

Populates the database with demo data for development and testing.

Usage:
    python manage.py seed_data

Creates:
- 1 superuser (admin)
- 3 demo users (editor, author_demo, user_demo)
- 5 categories (2 with children)
- 15 tags
- 30 posts (various statuses)
- 50 comments (nested)
- 3 site settings
"""

import random
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed the database with demo data for development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompt.",
        )

    def handle(self, *args, **options):
        if not options["no_input"]:
            confirm = input("This will DELETE all existing data and re-seed. Continue? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        self.stdout.write(self.style.NOTICE("Clearing existing data..."))
        self._clear_data()

        self.stdout.write(self.style.NOTICE("Seeding database..."))

        # 1. Users
        self._create_users()

        # 2. Categories
        self._create_categories()

        # 3. Tags
        self._create_tags()

        # 4. Posts
        self._create_posts()

        # 5. Comments
        self._create_comments()

        # 6. Site Settings
        self._create_site_settings()

        self.stdout.write(self.style.SUCCESS("\nDatabase seeded successfully!"))
        self.stdout.write("  Superuser: admin / admin@blog.com / admin123456")
        self.stdout.write("  Users: editor / author_demo / user_demo (password: demo123456)")
        self.stdout.write("  Run: python manage.py runserver")
        self.stdout.write("  Visit: http://localhost:8000/api/docs/")

    # ═══════════════════════════════════════════════
    # Data Creation Methods
    # ═══════════════════════════════════════════════

    def _clear_data(self):
        """Remove all existing data in correct order (respect FKs)."""
        from apps.comments.models import Comment, CommentLike
        from apps.blog.models import Post, Category, Tag, SiteSetting
        from apps.accounts.models import User, Subscriber
        from apps.media_library.models import Media

        CommentLike.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        Media.objects.all().delete()
        SiteSetting.objects.all().delete()
        Subscriber.objects.all().delete()
        User.objects.all().delete()

    def _create_users(self):
        """Create superuser and demo users."""
        from apps.accounts.models import User

        User.objects.create_superuser(
            username="admin",
            email="admin@blog.com",
            password="admin123456",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMIN,
            bio="Site administrator and lead developer.",
            email_verified=True,
            is_staff=True,
            is_superuser=True,
        )

        User.objects.create_user(
            username="editor",
            email="editor@blog.com",
            password="demo123456",
            first_name="Editor",
            last_name="Zhang",
            role=User.Role.EDITOR,
            bio="Senior content editor. I review and polish all articles.",
            email_verified=True,
        )

        User.objects.create_user(
            username="author_demo",
            email="author@blog.com",
            password="demo123456",
            first_name="Ming",
            last_name="Li",
            role=User.Role.AUTHOR,
            bio="Full-stack developer and tech writer. I love Python and open source.",
            email_verified=True,
            website="https://github.com/author_demo",
        )

        User.objects.create_user(
            username="user_demo",
            email="user@blog.com",
            password="demo123456",
            first_name="Regular",
            last_name="User",
            role=User.Role.USER,
            bio="A passionate reader who loves technology and design.",
            email_verified=True,
        )

        self.stdout.write(self.style.SUCCESS("  [OK] Created 4 users"))

    def _create_categories(self):
        """Create hierarchical categories."""
        from apps.blog.models import Category

        # Root categories
        tech = Category.objects.create(name="技术", slug="technology", description="技术文章与教程", order=1)
        life = Category.objects.create(name="生活", slug="life", description="生活感悟与分享", order=2)
        design = Category.objects.create(name="设计", slug="design", description="UI/UX 设计与用户体验", order=3)
        programming = Category.objects.create(name="编程", slug="programming", description="编程语言与开发工具", order=4)
        travel = Category.objects.create(name="旅行", slug="travel", description="旅行攻略与游记", order=5)

        # Subcategories under "技术"
        Category.objects.create(name="人工智能", slug="ai", description="AI & Machine Learning", parent=tech, order=1)
        Category.objects.create(name="前端开发", slug="frontend", description="Frontend Development", parent=tech, order=2)
        Category.objects.create(name="后端开发", slug="backend", description="Backend Development", parent=tech, order=3)

        self.stdout.write(self.style.SUCCESS("  [OK] Created 5 categories (3 subcategories)"))

    def _create_tags(self):
        """Create 15 tags."""
        from apps.blog.models import Tag

        tag_names = [
            "Python", "Django", "JavaScript", "Vue", "React", "TypeScript",
            "CSS", "Docker", "Kubernetes", "Git", "REST API", "GraphQL",
            "PostgreSQL", "Redis", "微服务",
        ]
        for name in tag_names:
            slug = name.lower().replace(" ", "-")
            Tag.objects.create(name=name, slug=slug)

        self.stdout.write(self.style.SUCCESS("  [OK] Created 15 tags"))

    def _create_posts(self):
        """Create 30 sample posts with various statuses."""
        from apps.blog.models import Post, Category, Tag
        from apps.accounts.models import User
        from django.utils.text import slugify

        author_admin = User.objects.get(username="admin")
        author_editor = User.objects.get(username="editor")
        author_demo = User.objects.get(username="author_demo")
        all_tags = list(Tag.objects.all())
        all_categories = list(Category.objects.filter(is_active=True))

        posts_data = [
            # Published posts (20)
            {
                "title": "Django 5.0 新特性完全指南",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "programming",
                "tag_names": ["Python", "Django"],
                "is_featured": True,
                "days_ago": 1,
            },
            {
                "title": "使用 Docker Compose 搭建微服务开发环境",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "backend",
                "tag_names": ["Docker", "微服务"],
                "is_featured": True,
                "days_ago": 3,
            },
            {
                "title": "Vue 3 Composition API 实战技巧",
                "status": "PUBLISHED",
                "author": author_editor,
                "category_slug": "frontend",
                "tag_names": ["Vue", "JavaScript", "TypeScript"],
                "is_featured": True,
                "days_ago": 5,
            },
            {
                "title": "PostgreSQL 查询优化实战：索引设计与 EXPLAIN 分析",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "backend",
                "tag_names": ["PostgreSQL", "Django", "Python"],
                "is_featured": False,
                "days_ago": 7,
            },
            {
                "title": "React 18 并发模式详解",
                "status": "PUBLISHED",
                "author": author_editor,
                "category_slug": "frontend",
                "tag_names": ["React", "JavaScript", "CSS"],
                "is_featured": True,
                "days_ago": 8,
            },
            {
                "title": "深入理解 Redis 数据结构与应用场景",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "backend",
                "tag_names": ["Redis", "Python"],
                "is_featured": False,
                "days_ago": 10,
            },
            {
                "title": "设计模式在 Python 项目中的实践",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "programming",
                "tag_names": ["Python"],
                "is_featured": False,
                "days_ago": 12,
            },
            {
                "title": "CSS Grid 布局完全指南",
                "status": "PUBLISHED",
                "author": author_editor,
                "category_slug": "frontend",
                "tag_names": ["CSS", "JavaScript"],
                "is_featured": False,
                "days_ago": 14,
            },
            {
                "title": "GraphQL vs REST API：如何选择",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "backend",
                "tag_names": ["GraphQL", "REST API", "Python"],
                "is_featured": False,
                "days_ago": 15,
            },
            {
                "title": "AI 编程助手对比：GitHub Copilot vs Cursor vs Claude",
                "status": "PUBLISHED",
                "author": author_admin,
                "category_slug": "ai",
                "tag_names": ["Python", "JavaScript"],
                "is_featured": True,
                "days_ago": 18,
            },
            {
                "title": "2025 年技术趋势展望",
                "status": "PUBLISHED",
                "author": author_admin,
                "category_slug": "technology",
                "tag_names": ["Python", "Docker", "微服务"],
                "is_featured": False,
                "days_ago": 20,
            },
            {
                "title": "TypeScript 高级类型体操",
                "status": "PUBLISHED",
                "author": author_editor,
                "category_slug": "frontend",
                "tag_names": ["TypeScript", "JavaScript"],
                "is_featured": False,
                "days_ago": 22,
            },
            {
                "title": "Kubernetes 入门到实践",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "backend",
                "tag_names": ["Kubernetes", "Docker", "微服务"],
                "is_featured": False,
                "days_ago": 25,
            },
            {
                "title": "如何写出优雅的 Git Commit Message",
                "status": "PUBLISHED",
                "author": author_admin,
                "category_slug": "programming",
                "tag_names": ["Git"],
                "is_featured": False,
                "days_ago": 28,
            },
            {
                "title": "远程办公两年后的思考",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "life",
                "tag_names": [],
                "is_featured": False,
                "days_ago": 30,
            },
            {
                "title": "设计师必知的 10 个配色原则",
                "status": "PUBLISHED",
                "author": author_editor,
                "category_slug": "design",
                "tag_names": ["CSS"],
                "is_featured": False,
                "days_ago": 35,
            },
            {
                "title": "日本旅行攻略：东京-京都-大阪",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "travel",
                "tag_names": [],
                "is_featured": False,
                "days_ago": 40,
            },
            {
                "title": "Django REST Framework 最佳实践",
                "status": "PUBLISHED",
                "author": author_demo,
                "category_slug": "backend",
                "tag_names": ["Django", "Python", "REST API"],
                "is_featured": True,
                "days_ago": 42,
            },
            {
                "title": "响应式设计：从移动优先到桌面适配",
                "status": "PUBLISHED",
                "author": author_editor,
                "category_slug": "design",
                "tag_names": ["CSS", "JavaScript"],
                "is_featured": False,
                "days_ago": 50,
            },
            {
                "title": "程序员健康指南：如何保护颈椎和视力",
                "status": "PUBLISHED",
                "author": author_admin,
                "category_slug": "life",
                "tag_names": [],
                "is_featured": False,
                "days_ago": 60,
            },
            # Draft posts (5)
            {
                "title": "正在写作中：WebAssembly 入门",
                "status": "DRAFT",
                "author": author_demo,
                "category_slug": "frontend",
                "tag_names": ["JavaScript"],
                "is_featured": False,
                "days_ago": 2,
            },
            {
                "title": "未完成：微服务架构的利与弊",
                "status": "DRAFT",
                "author": author_editor,
                "category_slug": "backend",
                "tag_names": ["微服务"],
                "is_featured": False,
                "days_ago": 5,
            },
            {
                "title": "草稿：2025 跨年总结",
                "status": "DRAFT",
                "author": author_admin,
                "category_slug": "life",
                "tag_names": [],
                "is_featured": False,
                "days_ago": 3,
            },
            {
                "title": "笔记：Rust 语言学习路径",
                "status": "DRAFT",
                "author": author_demo,
                "category_slug": "programming",
                "tag_names": [],
                "is_featured": False,
                "days_ago": 1,
            },
            {
                "title": "草稿：DevOps 工具链选择指南",
                "status": "DRAFT",
                "author": author_editor,
                "category_slug": "backend",
                "tag_names": ["Docker", "Git", "Kubernetes"],
                "is_featured": False,
                "days_ago": 10,
            },
            # Archived posts (3)
            {
                "title": "[已归档] 2023 年技术回顾",
                "status": "ARCHIVED",
                "author": author_admin,
                "category_slug": "technology",
                "tag_names": ["Python"],
                "is_featured": False,
                "days_ago": 365,
            },
            {
                "title": "[已归档] Flask vs Django 选择指南 (2023)",
                "status": "ARCHIVED",
                "author": author_demo,
                "category_slug": "programming",
                "tag_names": ["Python", "Django"],
                "is_featured": False,
                "days_ago": 400,
            },
            {
                "title": "[已归档] 旧版 Vue 2 项目迁移记录",
                "status": "ARCHIVED",
                "author": author_editor,
                "category_slug": "frontend",
                "tag_names": ["Vue", "JavaScript"],
                "is_featured": False,
                "days_ago": 500,
            },
            # Scheduled posts (2)
            {
                "title": "下周发布：最新 AI 工具测评",
                "status": "SCHEDULED",
                "author": author_admin,
                "category_slug": "ai",
                "tag_names": ["Python"],
                "is_featured": False,
                "days_ahead": 7,
            },
            {
                "title": "定时发布：开源项目推荐 2025",
                "status": "SCHEDULED",
                "author": author_demo,
                "category_slug": "programming",
                "tag_names": ["Git", "Python", "JavaScript"],
                "is_featured": False,
                "days_ahead": 14,
            },
        ]

        created_posts = []
        sample_content_templates = [
            lambda title: f"# {title}\n\n这是一篇关于 **{title}** 的详细文章。\n\n## 简介\n\n在这篇文章中，我们将深入探讨这个话题，分享实用的技巧和最佳实践。\n\n## 核心内容\n\n### 为什么重要\n\n这个主题对开发者来说非常重要，因为它直接影响到我们的开发效率和代码质量。\n\n### 具体实践\n\n```python\n# 示例代码\ndef hello():\n    print(\"Hello, World!\")\n    return True\n```\n\n### 最佳实践\n\n1. **保持代码简洁** — 好的代码就像好的文章，清晰易懂\n2. **遵循规范** — 使用业界公认的编码规范\n3. **持续学习** — 技术在不断演进\n\n## 总结\n\n希望这篇文章对你有所帮助！如果你有任何问题或建议，欢迎在评论区留言讨论。\n\n---\n\n*本文由作者原创，转载请注明出处。*",
        ]

        for i, data in enumerate(posts_data):
            title = data["title"]
            category = next((c for c in all_categories if c.slug == data.get("category_slug")), None)

            # Determine publish date
            if data["status"] == "SCHEDULED":
                days = data.get("days_ahead", 7)
                published_at = None
                scheduled_at = timezone.now() + timezone.timedelta(days=days)
            elif data["status"] == "PUBLISHED":
                days = data.get("days_ago", i * 3)
                published_at = timezone.now() - timezone.timedelta(days=days)
                scheduled_at = None
            else:
                published_at = None
                scheduled_at = None

            content = sample_content_templates[0](title)

            post = Post.objects.create(
                title=title,
                slug=f"{slugify(title)}-{uuid.uuid4().hex[:4]}",
                content=content,
                author=data["author"],
                category=category,
                status=data["status"],
                is_featured=data.get("is_featured", False),
                published_at=published_at,
                scheduled_at=scheduled_at,
                reading_time_minutes=random.randint(3, 15),
                view_count=random.randint(0, 5000) if data["status"] == "PUBLISHED" else 0,
            )

            # Assign tags
            tag_names = data.get("tag_names", [])
            for tag_name in tag_names:
                tag = next((t for t in all_tags if t.name == tag_name), None)
                if tag:
                    post.tags.add(tag)

            created_posts.append(post)

        self.stdout.write(self.style.SUCCESS(f"  [OK] Created {len(created_posts)} posts (20 published, 5 drafts, 3 archived, 2 scheduled)"))

    def _create_comments(self):
        """Create 50 comments (nested)."""
        from apps.blog.models import Post
        from apps.accounts.models import User
        from apps.comments.models import Comment

        published_posts = list(Post.objects.published())
        users = list(User.objects.all())[:4]  # All 4 users

        comment_texts = [
            "非常好的文章！受益匪浅，期待更多类似的内容。",
            "写得很有深度，特别是关于最佳实践的部分。收藏了！",
            "请问作者有计划写关于这个主题的进阶文章吗？",
            "我在实际项目中遇到了类似的问题，这篇文章给了我很大启发。",
            "能不能详细讲一下第三点？我在那里有些困惑。",
            "这个示例代码可以简化一下，我贴一个改进版本：```python\n# improved version\n```",
            "感谢分享！已经转发给我的团队了。",
            "请问这个方案在生产环境中实际效果如何？",
            "很好的一篇入门指南，建议新手都来看看。",
            "写得不错，但是关于最后一节我认为有更好的方案。",
            "文章排版很精美，请问用的什么 Markdown 编辑器？",
            "建议在下一个版本中加入更多的实战案例。",
            "看了三遍，每次都有新的收获！",
            "希望作者能出一个系列，系统地讲解这个话题。",
            "关于这个话题，我还推荐阅读 XXX 的文章，二者可以互补。",
        ]

        created = 0
        # Create top-level comments first
        top_level_comments = []
        for _ in range(15):
            post = random.choice(published_posts)
            author = random.choice(users)
            text = random.choice(comment_texts)

            comment = Comment.objects.create(
                post=post,
                author=author,
                content=text,
                is_approved=True,
                is_spam=False,
                ip_address=f"127.0.0.{random.randint(1, 255)}",
            )
            top_level_comments.append(comment)
            created += 1

        # Create nested replies
        for _ in range(35):
            parent = random.choice(top_level_comments)
            post = parent.post
            author = random.choice(users)

            # Don't reply to yourself
            if author == parent.author:
                author = random.choice([u for u in users if u != parent.author])

            text = random.choice([
                "同意你的观点！",
                "补充一下：在实际使用中还需要注意安全问题。",
                "说得对，我之前也遇到过这个问题。",
                "感谢回复，我明白了！",
                "这个角度很新颖，之前没想到过。",
            ])

            Comment.objects.create(
                post=post,
                author=author,
                parent=parent,
                content=text,
                is_approved=True,
                is_spam=False,
                ip_address=f"192.168.1.{random.randint(1, 255)}",
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"  [OK] Created {created} comments"))

    def _create_site_settings(self):
        """Create default site configuration."""
        from apps.blog.models import SiteSetting

        settings_data = [
            ("blog_title", "Person Blog", "站点标题"),
            ("blog_description", "一个关于技术、生活和设计的个人博客", "站点描述"),
            ("posts_per_page", 12, "每页文章数"),
            ("enable_comments", True, "是否启用评论"),
            ("comment_approval_required", True, "评论是否需要审核"),
            ("enable_newsletter", True, "是否启用订阅"),
            ("social_github", "https://github.com/youwo27", "GitHub 链接"),
            ("social_twitter", "", "Twitter 链接"),
        ]

        for key, value, desc in settings_data:
            SiteSetting.objects.create(key=key, value=value, description=desc)

        self.stdout.write(self.style.SUCCESS(f"  [OK] Created {len(settings_data)} site settings"))
