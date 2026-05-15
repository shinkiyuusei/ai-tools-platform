# AI 生成工具聚合平台

基于 PRD 初始化的前后端分离项目骨架：

- `backend`：Flask API 服务，统一前缀为 `/api/v1`
- `frontend`：Vite + Vue 3 前端应用
- `docker-compose.yml`：MySQL 8.0、MongoDB、Redis 本地开发环境

## 快速开始

1. 复制 `.env.example` 为 `.env` 并按需修改配置。
2. 启动基础依赖：

```bash
docker compose up -d
```

3. 启动后端：

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python run.py
```

4. 启动前端：

```bash
cd frontend
npm install
npm run dev
```

## 已初始化内容

- JWT 鉴权基础设施
- 统一错误响应与业务错误码
- MySQL / MongoDB / Redis 连接配置
- DeepSeek 适配层占位，支持思考模式与异步生成任务结构
- Axios 请求拦截器与基础 UI 组件目录
