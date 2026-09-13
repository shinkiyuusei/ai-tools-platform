# SillyTavern 兼容层

本包在 `ai-tools-platform` 后端上实现了 SillyTavern 接口文档第 4.2 节（角色 / 聊天 / 组 / 世界书）和第 4.3 节（设置 / 预设 / 主题 / 移动 UI / 快捷键 / 密钥）的全部路由，挂载路径与 SillyTavern 相同（`/api/characters`、`/api/chats`、`/api/groups`、`/api/worldinfo`、`/api/settings`、`/api/presets`、`/api/themes`、`/api/moving-ui`、`/api/quick-replies`、`/api/secrets`）。

## 启用与配置

配置项（`.env`）：

- `ST_COMPAT_ENABLED`：默认 `true`，设为 `false` 可整体关闭。
- `ST_COMPAT_DATA_DIR`：兼容数据根目录，默认 `backend/data/st_compat`。
- `ST_COMPAT_ALLOW_KEYS_EXPOSURE`：默认 `false`，控制 `/api/secrets/view` 和 `/api/secrets/find` 是否返回密钥原文。

## 认证与响应约定

- 鉴权沿用平台 JWT：请求头 `Authorization: Bearer <token>`，通过 `@jwt_required()` 保护。
- 响应体不套用平台的 `{code, message, data}` 包装，而是尽量还原 SillyTavern 的原始 JSON/文本/状态码，方便 ST 兼容客户端直接消费。
- 每个平台用户的数据隔离在 `ST_COMPAT_DATA_DIR/<user_id>/` 下。

## 数据目录（与 SillyTavern 文件布局一致）

```text
<user_id>/
  characters/          # <name>.png，卡片 JSON 写入 PNG tEXt（chara/ccv3）
  chats/<name>/        # <chatId>.jsonl，JSON Lines 聊天文件
  group chats/         # <groupId>.jsonl
  groups/              # <groupId>.json
  worlds/              # <world>.json
  settings.json        # 前端设置
  secrets.json         # 密钥
  themes/  movingUI/  QuickReplies/
  OpenAI Settings/  TextGen Settings/  NovelAI Settings/  KoboldAI Settings/
  instruct/  context/  sysprompt/  reasoning/
  backups/             # settings_<user_id>_*.json 快照
```

## 已实现接口

### 4.2

- `/api/characters`：`create`、`rename`、`edit`、`edit-avatar`、`edit-attribute`、`merge-attributes`、`delete`、`all`、`get`、`chats`、`import`、`duplicate`、`export`
- `/api/chats`：`save`、`get`、`rename`、`delete`、`export`、`import`、`group/import`、`group/get`、`group/info`、`group/delete`、`group/save`、`search`、`recent`
- `/api/groups`：`all`、`create`、`edit`、`delete`
- `/api/worldinfo`：`list`、`get`、`delete`、`import`、`edit`

### 4.3

- `/api/settings`：`save`、`get`、`get-snapshots`、`load-snapshot`、`make-snapshot`、`restore-snapshot`
- `/api/presets`：`save`、`delete`、`restore`
- `/api/themes`：`save`、`delete`
- `/api/moving-ui`：`save`
- `/api/quick-replies`：`save`、`delete`
- `/api/secrets`：`write`、`read`、`view`、`find`、`delete`、`rotate`、`rename`、`settings`

## 实现要点

- 角色卡采用 SillyTavern V2/V3 PNG 内嵌格式：读取时优先 `ccv3`，写入时同时写 `chara` 与 `ccv3` 两个 tEXt 块（`png_utils.py`，纯 Python 实现，无第三方图片依赖）。
- 聊天文件为 JSON Lines；`get` 会把 header 和消息原样返回；`search`/`recent`/`group/info` 返回与 SillyTavern 一致的 `ChatInfo` 结构。
- 密钥存储格式、掩码规则、轮换/删除语义与 SillyTavern `SecretManager` 一致。
- 文件名统一经过 `sanitize_filename`，目录拼接都有 `is_path_within` 包含校验，防止目录穿越。

## 与 SillyTavern 的已知差异

- 认证是平台 JWT 而非 ST 的 session + CSRF。
- `/api/characters/import` 目前支持 `png` 与 `json`；`yaml/yml/charx/byaf` 返回 `{error: true}`。
- `/api/presets/restore` 不携带内置默认预设，返回 `{isDefault: false, preset: {}}`。
- 角色头像的静态文件路由（ST 的 `/characters/<name>.png`）不在本层范围内，需要时可在应用层单独挂载。
