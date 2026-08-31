# Wang Guan Open

> [English](README_EN.md)

`wang-guan-open` 是私人 AI 网关项目的**源码公开、非商业版本**。最新私人 `wang-guan` 是功能母版：公开版尽量保留工程能力，只剥离作者本人的人格、关系、数据、UI 视觉与私有服务。

**本项目不是 OSI 定义下的 Open Source Software。** 使用 PolyForm Noncommercial License 1.0.0，仅授权非商业用途。禁止将本项目或衍生版本用于收费销售、收费 SaaS、商业托管或其他商业获利场景，完整条款见 `LICENSE`。

## 当前能力

公开版不是空骨架。目前已包含 OpenAI-compatible 流式网关、Context Builder、Supabase 持久化、分层记忆、Mem0 可选语义记忆、摘要/threads/提醒后台结构、多供应商多 Key、内部 Tool Calling、MCP session 复用、TG / QQ / 微信通用消息接入，以及一套**视觉上重新设计**的 MiniApp 管理台。

私人内容不会因为“功能恢复”重新塞回来。具体迁移状态见 `docs/MIGRATION_STATUS.md`。

## 快速开始

复制 `.env.example` 配置至少以下内容：

```env
API_SECRET=please-change-this
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

安装并运行：

```bash
pip install -r requirements.txt
python main.py
```

容器部署使用 `entrypoint.sh`，会同时运行实时消息进程 `main.py` 和独立后台进程 `background_main.py`。

### 安全

公网部署必须设置 `API_SECRET`。未设置时聊天接口默认拒绝请求，只有显式设置 `ALLOW_INSECURE_NO_SECRET=1` 才允许无鉴权访问。CORS 默认关闭；确实需要浏览器跨域时，用 `CORS_ALLOW_ORIGIN` 指定可信 Origin，不建议公网使用 `*`。

## Context 与客户端 system prompt

`SYSTEM_INJECTION_MODE` 支持：

- `prepend`：默认。网关 Context 在前，保留客户端 system
- `append`：客户端 system 在前，网关 Context 在后
- `replace`：完全替换客户端 system

公开版默认不会偷偷吞掉客户端自己的 Prompt。

Context 当前可组合：可配置 Persona、core/current/long_term 记忆、rolling summary、ACTIVE/DORMANT threads、时间，以及扩展 Provider。

## 模型与渠道

基础聊天可以直接用 `LLM_*`。也可以为聊天、后台、识图、主动任务、QQ、微信配置独立渠道。若使用 Supabase `llm_config` 表，可按 `active / bg_active / vision_active / free_activity_active / qq_active / wx_active` 分离供应商和模型。

MiniApp 提供供应商、多 Key、多 Model、Prompt / Context、流式测试、记忆、线索、提醒与后台维护视图。它保留的是**功能价值**，不是作者私人 UI；页面结构和视觉设计已经重新制作。

## Tool / MCP

公开版包含真实可执行的通用工具示例：记忆查询/写入、活动日志、提醒，以及可配置 MCP 天气/搜索示例。每个工具模块使用同一模式：

```python
SCHEMAS = [...]
DISPATCH = {...}
```

由 `free_tools.py` 聚合。`tools_base.py` 保留 MCP initialize / session 复用 / 失效重连机制。私人 MCP URL 不会写死在仓库里，请通过环境变量连接你自己的服务。

## 平台接入

- Telegram：Webhook、owner 限制、群聊、延迟聚合、工具循环
- QQ：OneBot v11 正向 WebSocket `/qq-ws`、私聊/群聊、基础 REPLY/AT 格式
- 微信：iLink 文本长轮询、context_token 持久化、owner 限制

媒体通用层提供 Vision / STT / TTS Provider helper。更完整的平台媒体细节会继续按最新私人版泛化恢复，状态写在 `docs/MIGRATION_STATUS.md`，不会用“删掉”冒充脱敏。

## 私人 Overlay

推荐维护两个层：

```text
wang-guan-open/       # 通用工程能力，源码公开
my-private-overlay/   # 只属于你的内容
├─ persona/
├─ prompts/
├─ ui/
├─ tools/
├─ integrations/
└─ private-config/
```

作者私人版中的专属人格、称呼、关系逻辑、真实 MiniApp UI、生活数据、私有 MCP、真实 ID/Key/Token、小家世界观等不会进入公开仓库。

### 关于秘密日记

私人版的秘密日记曾经不仅存在于单独模块，还可能通过 Tool Schema、worker import、后台 `[DIARY]` parser 等路径被触发。因此公开版不提供作者秘密日记的默认可用实现。扩展者当然可以按 Tool 范式自行实现自己的私有日记模块，但需要放在自己的私有 Overlay 中。

## 许可

PolyForm Noncommercial License 1.0.0。允许学习、研究、修改和非商业部署/分发；不允许商业销售、收费服务或商业托管。需要商业授权请单独取得作者许可。
