# SillyTavern 1.18.0 接口与实现方式说明

> 项目路径：`C:/Users/40935/Desktop/python/SillyTavern-release/`
> 本文基于该目录源码整理，覆盖：服务端启动/配置、REST API 全量路由、流式生成实现、前端核心 API、扩展/插件体系、数据格式与关键实现模式。

## 1. 项目总览

### 1.1 技术栈

- 运行时：Node.js >= 20，ESM 模块（`"type": "module"`）。
- 服务端：Express 4 + 大量中间件（helmet、compression、cookie-session、csrf-sync、multer、cors 等）。
- 前端：原生 ES Module + jQuery/jQuery UI，无前端框架；主文件是 `public/script.js`，核心库由 Webpack 打包成 `public/lib.js`。
- 数据：文件系统存储，按用户分目录（默认 `data/default-user/`）；用户元数据用 `node-persist` 存在 `data/_storage/`。
- 测试：Jest 单测 + Playwright E2E（`tests/`）。

### 1.2 入口与启动链

- `server.js`：解析命令行参数（`src/command-line.js`），设置 `globalThis.DATA_ROOT` / `COMMAND_LINE_ARGS`，然后动态导入 `src/server-main.js`。
- `src/server-main.js`：初始化 Express 应用、中间件、静态目录、路由挂载；随后按顺序执行：
  1. `initUserStorage`（node-persist 用户存储）
  2. DNS 顺序设置、目录创建
  3. 数据迁移（`migrateUserData`、`migrateSystemPrompts`、`migratePublicOverrides`、`verifySecuritySettings`）
  4. `preSetupTasks`：组聊天元数据迁移、内容检查、磁盘缓存校验、secrets 迁移、settings/stats 初始化、加载服务端插件（`loadPlugins`）、初始化 SSRF 过滤与请求代理、Webpack 编译前端 lib
  5. `ServerStartup.start()`：按配置启动 HTTP/HTTPS（可同时 IPv4/IPv6）
  6. `postSetupTasks`：打开浏览器、心跳文件、`serverEvents.emit(SERVER_STARTED)`
- `src/server-events.js`：全局 `process.serverEvents` 事件总线，目前唯一事件 `server-started`。

### 1.3 命令行参数（`src/command-line.js`）

常用参数（`node server.js --help` 可看全量）：

- `--dataRoot <path>` 数据根目录（默认 `./data`）
- `--port <n>`、`--listen`、`--listenAddress`、`--enableIPv4/--enableIPv6`
- `--ssl` + `--certPath/--keyPath/--keyPassphrase`
- `--whitelistMode`、`--basicAuthMode`、`--enableCorsProxy`、`--disableCsrf`
- `--requestProxy` / `--requestProxyUrl` / `--requestProxyBypass`
- `--heartbeatInterval`、`--enableKeepAlive`、`--dnsPreferIPv6`
- `--global`（全局模式，`src/server-global.js` 入口）

### 1.4 config.yaml 关键配置

`dataRoot`、`listen`、`port`、`ssl`、`whitelistMode`、`basicAuthMode`、`enableUserAccounts`、`enableDiscreetLogin`、`hostWhitelist`、`privateAddressWhitelist`（SSRF 白名单）、`sessionTimeout`、`cors`、`requestProxy`、`backups`、`thumbnails`、`performance`（磁盘缓存/请求压缩/懒加载）、`extensions.enabled/autoUpdate/models`、`enableServerPlugins`、`git.backend`、`openai/gemini/claude/ollama` 等模型参数、`logging`、`rateLimiting`、`forwardedHeaders`。

## 2. HTTP 服务约定

### 2.1 中间件链（`src/server-main.js`）

按注册顺序：

1. `helmet`（关闭 CSP）、`compression`、`response-time`
2. `bodyParser.json/urlencoded`，上限 500MB
3. CORS（`config.yaml > cors`）
4. Basic Auth（仅 `--listen --basicAuthMode`）
5. IP 白名单（`--whitelistMode`）
6. `hostWhitelist`（Host 头校验）
7. Access Log（仅监听模式）
8. `cookie-session`（签名会话，secret 从 `data/cookie-secret.txt` 读取）
9. `setUserDataMiddleware`：把 `request.user = { profile, directories }` 挂到请求上
10. CSRF（`X-CSRF-Token` 头，`GET /csrf-token` 获取；`--disableCsrf` 可关）
11. 静态资源：`/`（index.html）、`/login`、`/callback/:source?`、Webpack lib、`user.css`、`public/`
12. 公开用户路由：`/api/users/*`（list/login/recover）
13. `requireLoginMiddleware`：其后全部需要登录
14. `/proxy/:url(*)` CORS 代理（默认关闭）、`/version`、旧路由 308 重定向、全部私有 API 路由

### 2.2 上传约定

- 全局 `multer.single('avatar')`，上传暂存到 `<dataRoot>/_uploads/`，由 `multerMonkeyPatch` 处理。
- 文件名基本都经 `sanitize-filename` + `src/middleware/validateFileName.js` 校验（拒绝 `/`、`\`、NUL）。
- 静态文件路由会做路径包含检查（`isPathUnderParent`），防止目录穿越。

## 3. 用户、认证与数据目录

### 3.1 用户模型（`src/users.js`）

- 用户记录存于 node-persist（`data/_storage`），字段：`handle/name/created/password/admin/enabled/salt`。
- 密码用 `crypto.scryptSync(password, salt, 64)` 哈希；会话内带 `version`（账号哈希摘要），数据变更后旧会话失效。
- 默认用户 `default-user`（admin、无密码）；`enableUserAccounts: false` 时所有请求都按默认用户处理。

### 3.2 用户数据目录（`src/constants.js` 的 `USER_DIRECTORY_TEMPLATE`）

每个用户一个根目录 `<dataRoot>/<handle>/`，包含：`characters`、`chats`、`group chats`、`groups`、`worlds`、`User Avatars`、`backgrounds`、`assets`、`user/images`、`user/files`、`thumbnails/{bg,avatar,persona}`、`OpenAI Settings`、`TextGen Settings`、`NovelAI Settings`、`KoboldAI Settings`、`themes`、`movingUI`、`QuickReplies`、`instruct`、`context`、`reasoning`、`sysprompt`、`extensions`、`vectors`、`backups` 等。

### 3.3 静态文件路由（`src/users.js`）

以下前缀按当前用户目录提供文件：

- `/backgrounds/*`
- `/characters/*`（角色头像/JSON）
- `/User%20Avatars/*`
- `/assets/*`
- `/user/images/*`
- `/user/files/*`
- `/scripts/extensions/third-party/*`（先查用户扩展目录，再回退全局扩展目录 `public/scripts/extensions/third-party/`）

### 3.4 用户/账户 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/users/list` | 公开：列出启用的登录用户（登录页用） |
| POST | `/api/users/login` | 公开：登录，写入 session |
| POST | `/api/users/recover-step1` | 公开：忘记密码第一步 |
| POST | `/api/users/recover-step2` | 公开：重置密码 |
| POST | `/api/users/logout` | 退出登录 |
| GET | `/api/users/me` | 当前用户信息 |
| POST | `/api/users/change-avatar` | 修改用户头像 |
| POST | `/api/users/change-password` | 修改密码 |
| POST | `/api/users/change-name` | 修改显示名 |
| POST | `/api/users/backup` | 导出全量数据 ZIP |
| POST | `/api/users/reset-settings` | 重置设置 |
| POST | `/api/users/reset-step1/2` | 重置流程 |
| POST | `/api/users/get` | 管理员：用户列表 |
| POST | `/api/users/disable` / `enable` | 管理员：禁用/启用账户 |
| POST | `/api/users/promote` / `demote` | 管理员：授予/撤销 admin |
| POST | `/api/users/create` / `delete` | 管理员：创建/删除账户 |
| POST | `/api/users/slugify` | 管理员：校验/规范化 handle |

## 4. REST API 全量路由

> 除标注外均为登录后的 POST；旧版路由统一 308 重定向到新路由（见 `src/server-startup.js` 的 `redirectDeprecatedEndpoints`）。

### 4.1 基础/公共

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 首页（未登录跳转 `/login`） |
| GET | `/login` | 登录页 |
| GET | `/callback/:source?` | OAuth PKCE 回调（如 OpenRouter），307 回首页 |
| GET | `/csrf-token` | 获取 CSRF token |
| POST | `/api/ping` | 心跳/续期 session（`?extend`） |
| GET | `/version` | 版本信息 |
| GET/POST | `/proxy/:url(*)` | CORS 代理（需配置启用） |

### 4.2 角色/聊天/世界书

**`/api/characters`（`src/endpoints/characters.js`）**

`create`、`rename`、`edit`、`edit-avatar`、`edit-attribute`、`merge-attributes`、`delete`、`all`、`get`、`chats`、`import`、`duplicate`、`export`。

- 存储：`characters/<name>.json`（卡片数据）+ `characters/<name>.png`（头像，内含卡片元数据）。
- `all` 默认只返回摘要；`lazyLoadCharacters/useDiskCache` 配置决定是否浅加载。
- 导入支持 JSON / PNG（V1/V2/V3 卡片，见第 7 节）。

**`/api/chats`（`src/endpoints/chats.js`）**

`save`、`get`、`rename`、`delete`、`export`、`import`、`group/import`、`group/get`、`group/info`、`group/delete`、`group/save`、`search`、`recent`。

- 聊天文件为 JSON 数组：第 0 个元素是 header（含 `chat_metadata`），其余为消息对象。
- 消息字段：`name/mes/is_user/is_system/send_date/gen_started/gen_finished/swipes/swipe_info/swipe_id/extra` 等（`public/global.d.ts` 有完整类型）。
- `extra` 支持 API/model/推理内容/工具调用/媒体附件（files/media/image/video）等。

**`/api/groups`（`src/endpoints/groups.js`）**

`all`、`create`、`edit`、`delete`。组对象含 `members/disabled_members/chat_id/chats/generation_mode/activation_strategy` 等。

**`/api/worldinfo`（`src/endpoints/worldinfo.js`）**

`list`、`get`、`delete`、`import`、`edit`。文件为 `worlds/<name>.json`，结构 `{ entries: { <id>: entry } }`；entry 字段见 `char-data.js` 的 `v2DataWorldInfoEntry`（keys/content/constant/selective/insertion_order/enabled/position/extensions...）。

### 4.3 设置/预设/主题/UI

**`/api/settings`（`src/endpoints/settings.js`）**

`save`、`get`、`get-snapshots`、`load-snapshot`、`make-snapshot`、`restore-snapshot`。

- 主设置文件：`data/<user>/settings.json`（前端全局状态 + `extension_settings`）。
- 快照存到 `backups/settings_<handle>_<timestamp>.json`，每 10 分钟自动备份一次。

**`/api/presets`**：`save`、`delete`、`restore`（按类型目录存 JSON）。
**`/api/themes`**：`save`、`delete`。
**`/api/moving-ui`**：`save`。
**`/api/quick-replies`**：`save`、`delete`（`QuickReplies/` 目录 JSON）。
**`/api/secrets`（`src/endpoints/secrets.js`）**：`write/read/view/find/delete/rotate/rename/settings`；密钥存 `secrets.json`，默认不向客户端暴露原文（`allowKeysExposure` 可开）。

### 4.4 媒体与资源

**`/api/images`**：`upload`、`list/:folder?`、`folders`、`delete`（`user/images/`）。
**`/api/avatars`**：`get`、`delete`、`upload`（`User Avatars/`）。
**`/api/backgrounds`**：`all`、`folders`、`delete`、`rename`、`upload`。
**`/api/sprites`**：`GET get`、`delete`、`upload-zip`、`upload`（组头像精灵图）。
**`/api/assets`**：`get`、`download`、`delete`、`character`（扩展资源，`assets/`）。
**`/api/files`**：`sanitize-filename`、`upload`、`delete`、`verify`（`user/files/`）。
**`/api/image-metadata`**：`folders/get|create|set-thumbnails|update|delete|assign|unassign`、`/`（单条元数据）、`/all`、`/cleanup`。
**`/thumbnail`**：`GET` 缩略图服务（publicRouter + apiRouter），由 `@jimp` 生成并缓存到 `thumbnails/`。
**`/api/backups`**：`chat/get`、`chat/delete`、`chat/download`（聊天备份）。
**`/api/data-maid`**：`report`、`finalize`、`view`、`delete`（数据清理/去重报告）。

### 4.5 扩展管理

**`/api/extensions`（`src/endpoints/extensions.js`）**：`install`、`update`、`branches`、`switch`、`move`、`version`、`delete`、`GET discover`。

- 第三方扩展以 git 仓库形式安装：全局扩展放 `public/scripts/extensions/third-party/`（需 admin），用户扩展放 `<user>/extensions/`（URL 为 `/scripts/extensions/third-party/<name>/...`）。
- 安装时校验 manifest.json，支持指定 branch、浅克隆、更新、切分支、移动、删除。

### 4.6 模型后端 API

**`/api/backends/chat-completions`（`src/endpoints/backends/chat-completions.js`）**

`status`、`bias`、`generate`、`multimodal-models`（子路由）、`process`。

- 支持 source：openai、claude、openrouter、makersuite、vertexai、mistralai、cohere、deepseek、aimlapi、xai、chutes、minimax、electronhub、azure_openai、custom、ai21、perplexity、groq、nanogpt、pollinations、moonshot、fireworks、cometapi、zai、siliconflow、workers_ai。
- `/generate` 是核心：前端传 `messages + model + 采样参数 + chat_completion_source + stream`，服务端按 source 转发到上游 API；`stream=true` 时把上游 SSE 原样 pipe 给 Express 响应。

**`/api/backends/text-completions`（`src/endpoints/backends/text-completions.js`）**

`status`、`props`、`generate`，子路由 `ollama`、`llamacpp`、`tabby`。支持 ooba/vllm/aphrodite/koboldcpp/togetherai/openrouter/featherless/huggingface/generic 等类型（`TEXTGEN_TYPES`）。

**`/api/backends/kobold`（`src/endpoints/backends/kobold.js`）**

`generate`、`status`、`transcribe-audio`、`embed`。

**`/api/novelai`（`src/endpoints/novelai.js`）**：`status`、`generate`、`generate-image`、`generate-voice`。
**`/api/horde`（`src/endpoints/horde.js`）**：`text-workers`、`text-models`、`status`、`cancel-task`、`task-status`、`generate-text`、`sd-samplers`、`sd-models`、`caption-image`、`user-info`、`generate-image`。
**`/api/openrouter`**：`models/providers`、`models/multimodal`、`models/embedding`、`models/image`、`credits`、`image/generate`。
**`/api/nanogpt`**：`credits`、`models/providers`。
**`/api/azure`**：`list`、`generate`（Azure OpenAI 部署列表/生成）。

### 4.7 OpenAI 系多模态端点（`src/endpoints/openai.js`）

`caption-image`、`generate-voice`、`electronhub/generate-voice`、`electronhub/models`、`chutes/generate-voice`、`chutes/models/embedding`、`nanogpt/models/embedding`、`siliconflow/models/embedding`、`workers-ai/models/embedding`、`generate-image`、`generate-video`、`custom/*`（自定义兼容代理）、`transcribe-audio`、`groq|mistral|zai|chutes/transcribe-audio`。

### 4.8 Google/Anthropic/火山/海螺

- **`/api/google`**：`caption-image`、`list-voices`、`generate-voice`、`list-native-voices`、`generate-native-tts`、`generate-image`、`generate-video`（MakerSuite/Vertex）。
- **`/api/anthropic`**：`caption-image`。
- **`/api/volcengine`**：`generate-voice`（火山引擎 TTS）。
- **`/api/minimax`**：`generate-voice`。

### 4.9 图像生成（`/api/sd`，`src/endpoints/stable-diffusion.js`）

主路由：`ping`、`upscalers`、`vaes`、`samplers`、`schedulers`、`models`、`get-model`、`set-model`、`generate`、`sd-next/upscalers`。

子路由：`comfy`、`comfyrunpod`、`together`、`sdcpp`、`drawthings`、`pollinations`、`stability`、`huggingface`、`chutes`、`electronhub`、`nanogpt`、`bfl`、`falai`、`xai`、`aimlapi`、`zai`、`workersai`。

### 4.10 TTS/STT（`/api/speech`，`src/endpoints/speech.js`）

`recognize`（Whisper 等）、`synthesize`（本地 TTS/Edge 等），子路由 `pollinations`、`elevenlabs`。

### 4.11 翻译/搜索/分类/字幕

- **`/api/translate`**：`libre`、`google`、`yandex`、`lingva`、`deepl`、`onering`、`deeplx`、`bing`。
- **`/api/search`**：`serpapi`、`transcript`、`searxng`、`tavily`、`koboldcpp`、`serper`、`zai`、`visit`（网页抓取）。
- **`/api/extra/classify`**：`labels`、`/`（情感/分类模型）。
- **`/api/extra/caption`**：`/`（图像描述）。

### 4.12 Tokenizer（`/api/tokenizers`，`src/endpoints/tokenizers.js`）

本地/远程编码解码：

- SentencePiece 模型：`llama/nerdstash/nerdstash_v2/mistral/yi/gemma/jamba` 的 `encode/decode`
- tiktoken：`gpt2/encode|decode`
- Web tokenizers：`claude/llama3/qwen2/command-r/command-a/nemo/deepseek` 的 `encode/decode`
- OpenAI：`openai/encode|decode|count`
- 远程：`remote/kobold/count`、`remote/textgenerationwebui/encode`

### 4.13 向量检索（`/api/vector`，`src/endpoints/vectors.js`）

`query`、`query-multi`、`insert`、`list`、`delete`、`purge-all`、`purge`。

- 本地索引基于 `vectra`（`data/<user>/vectors/<collectionId>/`），向量来源（`SOURCES`）：transformers、openai、mistral、togetherai、nomicai、cohere、ollama、llamacpp、vllm、webllm、koboldcpp、extras、palm、vertexai、electronhub、openrouter、chutes、nanogpt、siliconflow、workers_ai。
- 批量插入按每批 10 条执行；索引损坏时自动删除并 307 重试重建。

### 4.14 内容管理（`/api/content`）

`importURL`、`importUUID`（从外部 URL/Chub UUID 导入内容，带域名白名单 `whitelistImportDomains`）。

### 4.15 旧版端点 308 重定向

`/createcharacter` → `/api/characters/create`，`/getcharacters` → `/api/characters/all`，`/savechat` → `/api/chats/save`，`/getworldinfo` → `/api/worldinfo/get`，`/getbackgrounds` → `/api/backgrounds/all` 等（完整列表见 `src/server-startup.js`）。

## 5. 生成与流式实现

### 5.1 前端生成链路

1. `public/script.js` 的 `Generate()` 组装上下文：角色卡、世界书、作者笔记、深度提示、正则替换、宏替换、聊天记录。
2. 按 `main_api` 选择通道：`kobold`、`koboldhorde`、`textgenerationwebui`、`novel`、`openai`；聊天补全额外按 `chat_completion_source` 分流。
3. 非流式：`sendGenerationRequest()` POST `/api/backends/*/generate`，拿完整 JSON。
4. 流式：`sendStreamingRequest()`（`public/script.js`）调用 `sendOpenAIRequest` / `generateTextGenWithStreaming` / `generateNovelWithStreaming` / `generateKoboldWithStreaming`。

### 5.2 SSE 流式

- 服务端：上游请求带 `stream: true`，`forwardFetchResponse(fetchResponse, response)` 把上游 body 原样转发到 Express 响应（不设置自己的 `text/event-stream`，直接把上游流 pipe 出去）。
- 前端：`public/scripts/sse-stream.js` 的 `EventSourceStream` 把 fetch 的二进制流按 `\n\n` 拆成 SSE 事件；`openai.js` 的 `getEventSourceStream` 消费 `delta`，`streaming-display.js` 平滑渲染，并派发 `STREAM_TOKEN_RECEIVED` 事件。
- 停止生成：AbortController 中断 fetch/上游连接，触发 `GENERATION_STOPPED`。

### 5.3 状态/能力探测

各后端有 `/status`（在线状态/模型列表）与 `/props`（text-completions 的模型能力），前端 `online_status` 事件驱动 UI 更新。

## 6. 前端核心接口

### 6.1 `globalThis.SillyTavern`

```js
globalThis.SillyTavern = {
    libs,        // webpack 打包的第三方库
    getContext,  // 扩展入口 API
};
```

### 6.2 `getContext()`（`public/scripts/st-context.js`）

扩展/脚本的主要入口，返回对象包含：

- 状态：`chat`、`characters`、`groups`、`name1/name2`、`characterId`、`groupId`、`chatId`、`onlineStatus`、`maxContext`、`chatMetadata`、`mainApi`。
- 聊天操作：`addOneMessage`、`deleteMessage`、`deleteLastMessage`、`updateMessageBlock`、`saveChat`、`openCharacterChat`、`openGroupChat`、`reloadCurrentChat`、`renameChat`、`sendSystemMessage`、`swipe.*`（left/right/to/show/hide/refresh/isAllowed/state）。
- 生成：`generate`、`sendStreamingRequest`、`sendGenerationRequest`、`stopGeneration`、`generateQuietPrompt`、`generateRaw`、`generateRawData`。
- 事件：`eventSource`、`eventTypes`。
- 命令：`SlashCommandParser`、`SlashCommand`、`SlashCommandArgument`、`SlashCommandNamedArgument`、`SlashCommandEnumValue`、`ARGUMENT_TYPE`、`executeSlashCommandsWithOptions`、`registerSlashCommand`（废弃）。
- 宏：`macros`（新引擎）、`registerMacro/unregisterMacro`（废弃的 MacrosParser）。
- 工具调用：`ToolManager`、`registerFunctionTool`、`unregisterFunctionTool`、`isToolCallingSupported`、`canPerformToolCalls`。
- 变量：`variables.local/global` 的 `get/set/del/add/inc/dec/has`。
- 世界书：`loadWorldInfo`、`saveWorldInfo`、`reloadWorldInfoEditor`、`updateWorldInfoList`、`convertCharacterBook`、`getWorldInfoPrompt`、`getWorldInfoNames`。
- 设置：`extensionSettings`、`chatCompletionSettings`、`textCompletionSettings`、`powerUserSettings`、`saveSettingsDebounced`、`writeExtensionField/Bulk`。
- UI/工具：`Popup`、`POPUP_TYPE`、`POPUP_RESULT`、`callGenericPopup`、`renderExtensionTemplate/Async`、`loader`、`showLoader/hideLoader`（废弃）、`getThumbnailUrl`、`t/translate/getCurrentLocale/addLocaleData`、`tags/tagMap`、`importFromExternalUrl`、`uuidv4`、`timestampToMoment`。
- 服务：`ChatCompletionService`、`TextCompletionService`、`ConnectionManagerRequestService`、`getPresetManager`、`getChatCompletionModel`、`registerDataBankScraper`。
- 常量：`symbols.ignore`、`constants.unset`。

### 6.3 `lib.js` 导出（`public/lib.js`）

`lodash`、`Fuse`、`DOMPurify`、`hljs`、`localforage`、`Handlebars`、`css`（@adobe/css-tools）、`Bowser`、`DiffMatchPatch`、`Readability`、`SVGInject`、`showdown`、`moment`、`seedrandom`、`Popper`、`droll`、`morphdom`、`slideToggle`、`chalk`、`yaml`、`chevrotain`、`gzip/gzipSync`、`sha256`；并给旧扩展挂 `window.Fuse/DOMPurify/hljs/localforage/Handlebars/showdown/moment/Popper/droll` 等兼容垫片。

### 6.4 事件（`public/scripts/events.js`）

`eventSource` 为 EventEmitter，`event_types` 定义 100 多个事件，主要分类：

- 生命周期：`APP_INITIALIZED`、`APP_READY`、`EXTENSIONS_FIRST_LOAD`、`EXTENSION_SETTINGS_LOADED`、`SETTINGS_LOADED/UPDATED`、`EXTRAS_CONNECTED`
- 消息：`MESSAGE_SENT/RECEIVED/EDITED/DELETED/UPDATED/SWIPED`、`USER_MESSAGE_RENDERED`、`CHARACTER_MESSAGE_RENDERED`、`MORE_MESSAGES_LOADED`
- 生成：`GENERATION_STARTED/STOPPED/ENDED`、`GENERATION_AFTER_COMMANDS`、`GENERATE_BEFORE_COMBINE_PROMPTS`、`GENERATE_AFTER_COMBINE_PROMPTS`、`GENERATE_AFTER_DATA`、`STREAM_TOKEN_RECEIVED`、`STREAM_REASONING_DONE`
- 角色/聊天/组：`CHARACTER_EDITED/DELETED/DUPLICATED/RENAMED`、`CHAT_CHANGED/LOADED/CREATED/DELETED/RENAMED`、`GROUP_UPDATED`、`GROUP_MEMBER_DRAFTED`
- 世界书/设置/API：`WORLDINFO_UPDATED`、`WORLD_INFO_ACTIVATED`、`CHATCOMPLETION_SOURCE_CHANGED`、`CHATCOMPLETION_MODEL_CHANGED`、`OAI_PRESET_CHANGED_BEFORE/AFTER`、`MAIN_API_CHANGED`、`ONLINE_STATUS_CHANGED`
- 扩展功能：`SD_PROMPT_PROCESSING`、`IMAGE_SWIPED`、`TOOL_CALLS_PERFORMED/RENDERED`、`SECRET_WRITTEN/DELETED/ROTATED/EDITED`、`TTS_JOB_STARTED/AUDIO_READY/COMPLETE`、`PERSONA_CHANGED/CREATED/UPDATED/RENAMED/DELETED`、`ITEMIZED_PROMPTS_LOADED/SAVED/DELETED`、`MEDIA_ATTACHMENT_DELETED`、`FILE_ATTACHMENT_DELETED`。

## 7. 扩展/插件体系

### 7.1 服务端插件（`src/plugin-loader.js`）

- 目录：`plugins/`，`config.yaml > enableServerPlugins: true` 时启动时自动加载。
- 模块协议（ESM 或 CJS，目录内找 `package.json.main` / `index.js|cjs|mjs`）：

```js
export const info = { id: 'my-plugin', name: 'My Plugin', description: '...' };
export async function init(router) { /* router.get('/ping', ...) */ }
export async function exit() { /* 清理 */ }
```

- 插件 ID 必须匹配 `^[a-z0-9_-]+$`；注册的路由挂载到 `/api/plugins/<id>/...`；`exit()` 在服务退出时统一调用。
- 支持 `enableServerPluginsAutoUpdate`（git 自动 pull）和 CLI `node plugins.js install|update`。

### 7.2 客户端扩展

**目录**：

- 内置扩展：`public/scripts/extensions/<name>/`（assets、attachments、caption、connection-manager、expressions、gallery、memory、quick-reply、regex、stable-diffusion、token-counter、translate、tts、vectors）。
- 第三方扩展：用户级 `<dataRoot>/<handle>/extensions/<repo>/`，全局级 `public/scripts/extensions/third-party/<repo>/`；URL 统一为 `/scripts/extensions/third-party/<repo>/...`。

**manifest.json 字段**（`public/scripts/extensions.js` 读取）：

`display_name`、`version`、`author`、`js`（入口，按 ES module 注入）、`css`、`i18n`（`{ locale: file }`）、`loading_order`、`requires`（需要 Extras API 提供的模块）、`dependencies`（依赖的其他扩展）、`minimum_client_version`、`optional`、`auto_update`、`hooks`（`{ hookName: globalFunctionName }`，如 `activate`/`clean`）、`generate_interceptor`（全局函数名，生成前钩子）。

**加载流程**：

1. `discoverExtensions()` 调 `/api/extensions/discover` 拿到扩展列表。
2. `getManifests()` 逐个拉 `manifest.json`。
3. `activateExtensions()` 校验客户端版本/模块/依赖/禁用状态，然后按 `loading_order` 注入 locale、CSS、`<script type="module">`，完成后调 `hooks.activate`。
4. 管理界面支持安装/更新/切分支/移动/删除/批量启停；`generate_interceptor` 扩展可在生成前修改 `chat`、`contextSize`、`abort`。

### 7.3 Extras API 集成

- 设置：`extension_settings.apiUrl`（默认 `http://localhost:5100`）+ `apiKey`。
- 连接：前端 GET `<apiUrl>/api/modules`，返回 `{ modules: [...] }`；`doExtrasFetch()` 自动带 Bearer token。
- 满足 `requires` 模块的扩展才会激活，激活后触发 `EXTRAS_CONNECTED`。

### 7.4 Slash 命令（`public/scripts/slash-commands.js`）

- 解析器：`SlashCommandParser`（chevrotain 词法/语法解析），命令对象 `SlashCommand.fromProps({ name, callback, aliases, namedArgumentList, unnamedArgumentList, helpString, returns, checkPermission, enumProviders })`。
- 旧接口 `registerSlashCommand(name, callback, helpString, ...)` 已废弃，仍可用。
- 特性：命名参数（`--key=value`）、枚举自动补全（`SlashCommandEnumValue`）、闭包参数（`SlashCommandClosure`）、管道、返回值（`pipe`）、权限检查、abort 控制器。
- 内置命令数百个：`/api`、`/send`、`/gen`、`/swipe`、`/impersonate`、`/set`、`/getvar`、`/world`、`/loader-wrap` 等，`/help` 查看。

### 7.5 宏（Macros）

- 旧：`MacrosParser.registerMacro(key, value|fn, description)`（`{{key}}` 替换，值可为函数，函数接收 nonce）。
- 新：`macros.registry.registerMacro(name, { category, description, handler })`（`public/scripts/macros/macro-system.js`），支持参数宏、类型化参数、动态宏（`substituteParams({ dynamicMacros })`）。
- 内置宏：`{{user}}`、`{{char}}`、`{{time}}`、`{{random}}`、`{{roll}}`、`{{input}}`、`{{lastMessage}}`、`{{group}}`、`{{persona}}`、`{{instruct}}`、`{{maxPrompt}}` 等（`macros.js` 的 `registerMacros`）。

### 7.6 Action Loader（`public/scripts/action-loader.js`）

- `loader.show({ blocking, toastMode, slug, message, title, onStop, onHide, overlayContent })` 返回 `ActionLoaderHandle`。
- `handle.stop()/hide()`；`loader.hide(handle?)`、`loader.active`、`loader.get(id)`、`loader.isBlocking`。
- 多个 loader 可叠加：单个遮罩 + 各自 toast；配合 `/loader-wrap` 等 slash 命令使用。

### 7.7 其他扩展 API

- Quick Reply：`window.quickReplyApi`（`public/scripts/extensions/quick-reply/api/QuickReplyApi.js`）。
- 变量：`variables.js` 全局/局部变量（get/set/del/add/inc/dec/has），有对应 slash 命令。
- 工具调用：`tool-calling.js` 的 `ToolManager.registerFunctionTool(name, { callback, description, parameters })`，支持 OpenAI/Claude/Gemini 函数调用与自动执行。
- 正则脚本：`extensions/regex/engine.js` 的 `getRegexedString`、`regex_placement`。
- 模板：`renderExtensionTemplate(extName, templateId, data)` / `Async`，模板目录 `scripts/extensions/<extName>/*.html`。

## 8. 数据格式

### 8.1 角色卡

- V1：顶层 `name/description/personality/scenario/first_mes/mes_example/creatorcomment/tags/talkativeness/fav/create_date`。
- V2：`{ spec: 'chara_card_v2', spec_version: '2.0', data: { ...V1 字段, creator_notes, system_prompt, post_history_instructions, alternate_greetings, creator, character_version, tags, extensions, character_book } }`。
- V3：`spec: 'chara_card_v3'`，`spec_version >= 3.0`，`data` 更宽松。
- PNG 内嵌：`tEXt` 块，keyword `chara`（V2）/ `ccv3`（V3），base64(JSON)；读取优先 `ccv3`，写入同时写两版（`src/character-card-parser.js`）。
- 校验器：`src/validator/TavernCardValidator.js`（V1/V2/V3 字段检查）。

### 8.2 聊天

`chats/<chatId>.json` 为 JSON 数组；`[0]` 是 header（`chat_metadata`），后面每条消息含 `name/mes/is_user/is_system/swipes/swipe_id/extra`；`extra` 可含 API/model/推理/工具调用/附件。组聊天存 `group chats/<chatId>.json`。

### 8.3 世界书

`worlds/<name>.json`：`{ entries: { id: entry } }`。entry 关键字段：`keys`、`secondary_keys`、`content`、`constant`、`selective`、`insertion_order`、`enabled`、`position`、`extensions`（概率/深度/分组/递归控制等，见 `char-data.js` 的 `v2DataWorldInfoEntryExtensionInfos`）。

### 8.4 设置与快照

- `settings.json`：前端全部设置（`power_user`、各 API settings、`extension_settings`）。
- `backups/settings_<handle>_<timestamp>.json`：每 10 分钟自动快照 + 手动快照；`make-snapshot` 可另存。
- 预设目录：`OpenAI Settings/`、`TextGen Settings/`、`NovelAI Settings/`、`KoboldAI Settings/`、`instruct/`、`context/`、`reasoning/`、`sysprompt/`。

### 8.5 密钥

`secrets.json`：`{ [secretId]: { key, value, createdAt, lastUsedAt } }`；服务端按 `SECRET_KEYS`（openai/openrouter/anthropic/cohere/custom 等）读取，普通用户不可见原文。

### 8.6 统计

`stats.json`：按日期统计消息数/输入输出 token 等（`/api/stats` get/update/recreate）。

## 9. 关键实现模式

- **按用户目录映射**：`getUserDirectories(handle)` 从模板克隆路径并缓存（`DIRECTORIES_CACHE`），所有 API 通过 `request.user.directories` 定位文件。
- **安全文件 IO**：`write-file-atomic` 原子写、`sanitize-filename`、`isPathUnderParent` 越界检查、文件名中间件校验、上传目录清理（`cleanUploads`）。
- **SSRF 防护**：`src/private-request-filter.js` 自定义 HTTP(S) Agent，DNS 解析后拦截私有网段请求，支持 CIDR 白名单；`request-proxy.js` 通过 `proxy-agent` 全局替换 `http/https.globalAgent`。
- **迁移机制**：启动时执行旧数据迁移（公共目录→用户目录、secrets、组元数据、系统提示词、公共覆盖等），迁移前自动备份。
- **缩略图/磁盘缓存**：`endpoints/thumbnails.js` + `characters.js` 的 diskCache，`performance.*` 配置控制容量与懒加载；图片处理用 `@jimp`。
- **备份**：`archiver` 流式打 ZIP（用户全量备份/聊天备份），聊天备份带完整性校验与节流。
- **请求压缩**：`request-compression.js` 对大数据 payload 用 gzip 压缩后传输（`performance.requestCompression`）。
- **Tokenizers**：本地 SentencePiece 模型 + `tiktoken` + `@agnai/web-tokenizers`，也支持远程 kobold/text-generation-webui 计数。
- **前端打包**：Webpack 只打包 `public/lib.js`（配置见 `webpack.config.js`），开发/启动时 `webpack-serve` 中间件编译并带 cache buster。
- **心跳与健康检查**：`heartbeat.json` 定时写入，`src/healthcheck.js` 检查文件新旧。
- **限流**：`rate-limiter-flexible`（登录/恢复密码/Basic Auth 尝试次数，`Retry-After` 头）。

## 10. 测试

- `tests/`：Jest（`mock-server.test.js`、`prompt-converters.test.js`、`tavern-card-validator.test.js`、`util.test.js` 等）。
- `tests/frontend/`：Playwright E2E，重点覆盖宏引擎（MacroLexer/Parser/Registry/Engine、`MacroEngine.e2e.js` 等）。

## 11. 快速参考：做扩展最常用的文件

- 前端入口：`public/script.js`、`public/scripts/extensions.js`、`public/scripts/st-context.js`
- 服务端路由：`src/server-startup.js`（挂载清单）、`src/endpoints/*`
- 生成后端：`src/endpoints/backends/chat-completions.js`、`text-completions.js`、`kobold.js`
- 数据模型：`public/global.d.ts`、`public/scripts/char-data.js`
- 插件：`plugins/` + `src/plugin-loader.js`；扩展：`public/scripts/extensions/` + manifest.json
