# Wang Guan Open

> [English](README_EN.md)

Wang Guan Open 是一个面向个人 AI 的通用网关与运行框架。

它负责把模型供应商、聊天客户端、消息平台、上下文、记忆、工具调用和后台任务接到同一套系统里。对外提供 OpenAI-compatible API，也可以直接接入 Telegram、QQ、微信等消息入口。

如果你想做一个长期运行、带记忆、能接多个模型和多个聊天入口、还能继续自己扩展工具与后台能力的 AI，这个项目可以作为底座。

## 主要能力

### OpenAI-compatible 网关

提供：

```text
POST /v1/chat/completions
```

支持：

- SSE 流式输出
- OpenAI-compatible 请求格式
- reasoning 内容兼容
- 上游超时处理
- 多 Key 失败轮换
- 客户端自带 Tool 的透明转发
- 可选的网关内部 Tool Calling

### 多供应商 / 多模型

可以配置多个模型供应商，每个供应商支持：

- Base URL
- 多个 API Key
- 多个 Model
- 当前使用模型
- 自定义 Headers

同时支持不同用途使用不同模型渠道：

- chat
- background
- vision
- proactive
- QQ
- WeChat

既可以通过环境变量配置，也可以使用 Supabase `llm_config`，或者直接在 MiniApp 中管理通用 Runtime Provider。

### Context Builder

每次调用模型前，可以自动组合上下文，包括：

- System Prompt
- Persona Profile
- `core / current / long_term` 分层记忆
- 跨平台滚动摘要
- `ACTIVE / DORMANT` threads
- 当前时间
- 自定义 Context Provider

额外数据源可以通过 Provider 接口继续扩展，不需要把所有逻辑硬塞进主文件。

### 记忆与对话维护

支持 Supabase 持久化，并提供：

- 对话历史保存
- 分层记忆
- 可选 Mem0 语义记忆
- 日总结
- current 记忆刷新
- threads 扫描与状态维护
- 跨平台消息批量压缩
- 滚动摘要定期合并
- 长期记忆抽取
- 近期摘要窗口维护

适合长时间运行，而不是每次启动都从零开始。

### Tool Calling / MCP

内部工具统一使用：

```python
SCHEMAS = [...]
DISPATCH = {...]
```

由 `free_tools.py` 聚合。

项目同时提供 MCP 调用基础设施，包括：

- initialize
- session 复用
- `Mcp-Session-Id`
- session 失效后重新初始化
- JSON / SSE MCP 响应解析

仓库里附带通用示例，可以按同样结构接自己的工具或 MCP 服务。

### 消息平台

目前包含：

- Telegram Webhook
- Telegram 私聊 / 群聊
- QQ OneBot v11 正向 WebSocket
- QQ 私聊 / 群聊
- QQ REPLY / AT 格式
- 微信 iLink 文本长轮询
- 微信 `context_token` 持久化
- 消息延迟聚合
- 平台内 Tool Calling

### 图片 / 语音基础能力

提供通用媒体 helper：

- Vision
- STT
- TTS

具体平台的图片、语音、引用、表情等能力可以继续往现有适配层扩展。

### Reminders 与后台任务

独立后台进程负责周期任务，包括：

- reminders 检查与投递
- daily / weekly recurring reminders
- 夜间总结
- 跨平台消息压缩
- 滚动摘要维护

`entrypoint.sh` 会同时启动实时网关进程和后台进程。

### MiniApp 管理台

项目自带一个轻量管理页面，可用于：

- 配置模型供应商
- 管理多个 API Key
- 管理多个 Model
- 切换当前模型
- 编辑 System Prompt
- 预览完整 Context
- 查看 memories
- 查看 threads
- 查看 reminders
- 手动触发总结 / 压缩
- 测试流式聊天
- 导入 / 导出 Runtime 配置

访问：

```text
/miniapp
```

## 快速开始

复制 `.env.example`，至少配置：

```env
API_SECRET=please-change-this
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

安装依赖：

```bash
pip install -r requirements.txt
```

运行：

```bash
python main.py
```

如果需要同时运行后台任务：

```bash
./entrypoint.sh
```

Docker 也已经包含对应启动方式。

## 常用配置

### 网关

```env
API_SECRET=
PORT=8000
UPSTREAM_READ_TIMEOUT=180
SYSTEM_INJECTION_MODE=prepend
PERSIST_CONVERSATIONS=1
```

`SYSTEM_INJECTION_MODE` 支持：

- `prepend`
- `append`
- `replace`

### 默认模型

```env
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

### 独立模型渠道

```env
CHAT_BASE_URL=
CHAT_API_KEY=
CHAT_MODEL=

BG_CHAT_BASE_URL=
BG_CHAT_API_KEY=
BG_CHAT_MODEL=

VISION_BASE_URL=
VISION_API_KEY=
VISION_MODEL=

PROACTIVE_BASE_URL=
PROACTIVE_API_KEY=
PROACTIVE_MODEL=

QQ_LLM_BASE_URL=
QQ_LLM_API_KEY=
QQ_LLM_MODEL=

WX_LLM_BASE_URL=
WX_LLM_API_KEY=
WX_LLM_MODEL=
```

未单独配置的渠道会回退到通用聊天模型。

### Supabase

```env
SUPABASE_URL=
SUPABASE_KEY=
```

用于对话、记忆、threads、reminders、摘要和部分运行配置持久化。

### Telegram

```env
TG_BOT_TOKEN=
TG_OWNER_ID=
TG_GROUP_IDS=
TG_WEBHOOK_SECRET=
```

### QQ

```env
QQ_WS_TOKEN=
QQ_BOT_ID=
QQ_OWNER_ID=
QQ_GROUP_IDS=
```

OneBot v11 WebSocket 地址：

```text
/qq-ws
```

### 微信

```env
WX_ILINK_TOKEN=
WX_ILINK_BOT_ID=
WX_OWNER_ID=
```

## 扩展方式

这个项目更适合继续往上加东西，而不是修改一坨核心代码。

常见扩展入口：

```text
Context Provider  -> 增加新的上下文来源
Tool Module       -> 增加新的函数工具
MCP               -> 接外部能力
Platform Adapter  -> 接新的聊天平台
Background Task   -> 增加周期任务
MiniApp           -> 增加自己的管理功能
```

保持各模块职责分开，后续升级会轻松很多。

## License

PolyForm Noncommercial License 1.0.0。

允许学习、研究、修改和非商业部署 / 分发；商业销售、收费 SaaS、收费托管或其他商业用途不在许可范围内。完整条款见 `LICENSE`。
