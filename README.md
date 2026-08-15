# AI 互动叙事聊天平台

沉浸式 AI 角色扮演与互动小说平台。选择世界观与角色，进入由 DeepSeek / Gemini 驱动的第一人称叙事聊天——AI 实时追踪好感度、欲望值等角色状态，每轮输出叙事正文 + 状态栏 + 选择分支。

> **内容警告：18+ / NSFW** — 本项目面向成人用户，包含成人向互动叙事内容。未成年人请勿使用。

## 核心功能

- **互动叙事聊天** — 流式 SSE 实时生成沉浸式第一人称叙事，支持思考模式（reasoning），AI 在叙事中自动推进角色状态变化
- **世界观创作** — 自定义世界设定、角色档案（外观 / 性格 / 语气 / 背景）、主角人设、核心冲突与初始场景，构建完整的互动小说场景
- **发现与推荐** — 排行榜、分类浏览、热门趋势、个性化推荐，探索社区中的互动叙事作品
- **角色状态追踪** — 好感度、欲望值等数值随剧情自动变化，持久化存储于对话中
- **多视角切换** — 同一作品中自由切换扮演角色，体验不同视角的叙事
- **多语言** — 支持简体中文、English、日本語、한국어，后端 i18n 全覆盖
- **用户系统** — JWT 注册/登录、收藏/喜欢/评分、个人中心与生成记录
- **管理后台** — 标签管理、作品 CRUD、角色卡管理
- **扩展系统** — 浏览器沙箱内加载社区扩展，支持 hook 订阅、UI 组件注入与受控 HTTP 代理

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite 8 + Vue Router 5 + Pinia 3 + Vue I18n + Axios |
| **后端** | Flask 3 + Flask-JWT-Extended + Flask-CORS + Flask-Babel |
| **数据库** | MySQL 8.0 |
| **AI** | DeepSeek API（`deepseek-v4-flash` / `deepseek-v4-pro`）、Gemini API（`[YDE]gemini-3.1-flash-防截断-0.5`），可切换 provider |
| **扩展** | 扩展沙箱 + 市场（hook / UI 组件 / HTTP 代理） |
| **容器** | Docker Compose（MySQL） |

## 快速开始

### 1. 环境准备

```bash
git clone <repo-url>
cd ai-tools-platform
cp .env.example .env   # 编辑 .env 填入 API Key 等配置（DeepSeek 与 Gemini 按需配置）
```

### 2. 启动基础依赖（Docker）

```bash
docker compose up -d
```

启动 MySQL 8.0（本机端口 `3306`）。

### 3. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py               # 默认 http://localhost:5000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev                 # 默认 http://localhost:5173
```

浏览器打开前端地址即可使用。

## 项目结构

```
ai-tools-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API 蓝图
│   │   ├── core/            # 配置（config.py）
│   │   ├── extensions/      # Flask 扩展初始化
│   │   ├── middlewares/     # 安全、i18n、响应中间件
│   │   ├── services/        # 业务逻辑层
│   │   │   ├── ai/          # AI 适配器（DeepSeek / Gemini）
│   │   │   ├── chat/        # 叙事 Prompt 构建器与聊天运行时
│   │   │   ├── credit.py    # 积分扣减与余额校验
│   │   │   ├── usage.py     # token 用量与每日统计
│   │   │   └── world_info.py# 世界设定（Lore）检索
│   │   └── utils/           # 工具函数（日志、响应）
│   ├── translations/        # i18n 翻译文件
│   ├── uploads/             # 上传文件目录
│   └── run.py               # 应用入口（同目录另有一键导入/抓取脚本，已归档至 git 历史）
├── frontend/
│   └── src/
│       ├── api/             # API 请求层
│       ├── components/      # 通用组件
│       ├── composables/     # 共享会话逻辑（useChatSession）
│       ├── config/          # AI provider / model 注册表
│       ├── router/          # 路由配置
│       ├── services/        # 扩展加载器与沙箱
│       ├── stores/          # Pinia 状态管理（auth / toast）
│       ├── utils/           # SSE 读取、消息渲染、通知等工具
│       └── views/           # 页面视图
├── database/                # 数据库初始化 SQL
├── docker-compose.yml       # 本地开发容器编排
├── .env.example             # 环境变量模板
└── README.md
```

## 配置说明

编辑项目根目录下的 `.env` 文件：

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_DB_PORT=3306
MYSQL_DB_USER=ai_user
MYSQL_DB_PASSWORD=ai_pass_123
MYSQL_DB_NAME=ai_tools_platform

# DeepSeek（必填）
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-v4-flash
DEEPSEEK_REASONER_MODEL=deepseek-v4-pro

# Gemini（使用 Gemini provider 时必填）
GEMINI_API_KEY=sk-xxxxxxxx
GEMINI_API_BASE=https://api.gemini.example.com/v1
GEMINI_CHAT_MODEL=[YDE]gemini-3.1-flash-防截断-0.5
GEMINI_PRO_MODEL=[YDE]gemini-3.1-flash-防截断-0.5

# 默认 AI provider：deepseek / gemini
DEFAULT_AI_PROVIDER=deepseek
```

`SECRET_KEY`、`JWT_SECRET_KEY`、`DEEPSEEK_API_KEY` 三项务必按实际环境修改；`GEMINI_API_KEY` 在使用 Gemini provider 时同样需要在 `.env` 中配置。

## 许可证

MIT
