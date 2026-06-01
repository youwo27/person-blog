# Person Blog

> 企业级个人博客系统 — 基于 Django 5 + Django REST Framework 构建

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | Django 5 + Django REST Framework 3.15 |
| 数据库 | PostgreSQL 16 (开发可回退 SQLite) |
| 缓存 | Redis 7 |
| 异步任务 | Celery + Redis |
| 认证 | djangorestframework-simplejwt (JWT) |
| API 文档 | drf-spectacular (OpenAPI 3.0 / Swagger) |
| 对象存储 | AWS S3 / MinIO (django-storages) |
| 容器化 | Docker + docker-compose |
| 代码质量 | ruff + mypy + pre-commit |
| 测试 | pytest + pytest-django + factory-boy |

## 快速开始

### 前置条件

- Python 3.12+
- PostgreSQL 16 (可选，默认使用 SQLite)
- Redis 7 (可选，开发环境无需启动)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/youwo27/person-blog.git
cd person-blog

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 3. 安装依赖
pip install -r backend/requirements/development.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少设置 SECRET_KEY

# 5. 数据库迁移
cd backend
python manage.py migrate

# 6. 启动开发服务器
python manage.py runserver

# 7. 访问
# API 文档: http://localhost:8000/api/docs/
# 健康检查: http://localhost:8000/api/health/
```

### 常用命令

```bash
make help          # 查看所有可用命令
make run           # 启动开发服务器
make migrate       # 执行数据库迁移
make test          # 运行测试
make lint          # 代码检查
make format        # 代码格式化
make build         # 构建 Docker 镜像
make up            # 启动 Docker 服务
```

## 项目结构

```
person-blog/
├── backend/                    # Django 项目根
│   ├── config/                 # Django 配置
│   │   └── settings/           # 分层配置 (base/dev/staging/prod)
│   ├── apps/                   # 应用模块
│   │   ├── accounts/           # 用户 & 认证
│   │   ├── blog/               # 文章 & 分类 & 标签
│   │   ├── comments/           # 评论系统
│   │   ├── media_library/      # 媒体管理
│   │   ├── search_index/       # 搜索
│   │   └── notifications/      # 通知系统
│   ├── common/                 # 共享模块 (分页/权限/异常/限流)
│   ├── tasks/                  # Celery 异步任务
│   └── requirements/           # 分层依赖 (base/dev/prod)
├── docker/                     # Docker 配置
├── .env.example                # 环境变量模板
├── pyproject.toml              # Python 工具链配置
└── Makefile                    # 常用命令
```

## API 文档

启动开发服务器后访问：
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## License

MIT License
