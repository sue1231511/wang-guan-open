# 最新私人版 → 源码公开版功能迁移表

原则：`wang-guan` 最新版是唯一功能母版。功能默认保留；只有私人内容才替换成环境变量、通用示例、扩展接口或注释。禁止用“删除整个模块”代替脱敏。

## 已恢复

- OpenAI-compatible `/v1/chat/completions`
- SSE 流式转发、`[DONE]` 检测、上游超时
- `reasoning_content` → `<think>` 兼容
- 可配置 system 注入策略：prepend / append / replace
- Runtime 多供应商、多 Key、多 Model 管理
- 公共工具的真实 Schema + Dispatch + 工具循环
- Supabase REST 持久化底层
- 对话历史持久化
- Persona / layered memories / rolling summary / threads 的 Context 组合
- Mem0 可选语义记忆
- 日总结、current 层刷新、threads 扫描、跨平台批量压缩
- reminders 数据与检查器基础
- 独立后台进程 + 共享线程池结构
- Telegram webhook、owner 限制、群聊 PASS、延迟聚合、工具循环
- QQ OneBot v11 正向 WebSocket、owner 限制、群聊 PASS、工具循环、REPLY/AT 格式
- 微信 iLink 文本长轮询、context_token 持久化、owner 限制、延迟聚合
- 通用 Vision / STT / TTS provider helper
- MiniApp：供应商、Key/Model、Prompt/Context、流式测试、记忆、线索、提醒、后台维护、配置导入导出
- MCP session 复用范式与可配置 MCP 示例

## 必须继续从最新版泛化恢复

这些属于通用工程能力，不允许因为脱敏而直接消失：

- 周 / 月 / 年总结与 persona reflection 的完整调度细节
- platform rolling summary maintenance + 长期记忆抽取 + 30 天窗口细节
- 完整 provider/key 失败记账及 provider-level rotation RPC 配套说明/迁移 SQL
- Telegram / QQ / 微信的图片、语音、引用等完整媒体链（通用媒体底层已恢复）
- QQ 戳一戳、群成员缓存恢复、真实群昵称/owner alias 的完整边界处理
- 微信 iLink 登录示例、图片/语音 CDN 示例
- 主动思考与自由活动完整状态机：轮次、重复动作检测、活动日志收尾、失败诊断
- 邮件、日历、天气、搜索、语音等通用工具示范实现
- MiniApp 中对应上述功能的通用管理页

## 私人内容：不得作为默认可用实现公开

下列内容不是“漏功能”，而是明确的私人 Overlay：

- 私人人格 Prompt 原文、专属关系与称呼
- 私人 MiniApp 视觉设计 / CSS / 页面构图
- 私人数据库内容、真实 ID、Token、Key、联系人
- 设备/健康/位置/排班的真实数据
- 私有 MCP 地址及私人工具业务实现
- 私人小家、宠物、世界观内容
- **秘密日记的实际实现与自动写入行为**

### 日记专项检查

公开前必须同时检查，不得只搜 `secret_diary.py`：

1. `secret_diary` Tool Schema / Dispatch
2. worker 中对 diary tool 的 import / 拼接
3. `[DIARY]...[/DIARY]` 这类隐藏 parser
4. proactive/free-activity 中的自动写 diary 逻辑
5. MiniApp diary 页面与 API
6. scheduled/background task 的 diary 调用

公开版可以在文档中示范“如何做一个自定义私有工具”，但不得默认提供可写入作者私人日记结构的代码。
