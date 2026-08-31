# Wang Guan Open

> [English](README_EN.md)

`wang-guan-open` 是从私人 AI 网关项目中剥离出的**源码公开版**。

它公开的是通用工程结构、接口设计与扩展方式，不包含原私人项目中的人格、关系设定、专属 UI、私人记忆、生活数据、私有工具和服务配置。

**本项目不是 OSI 定义下的 Open Source Software。** 代码采用 PolyForm Noncommercial License 1.0.0，仅允许非商业用途。禁止将本项目或其衍生版本用于收费销售、商业化服务或其他商业用途。详见 `LICENSE`。

---

## 1. 项目定位

这是一个可自行扩展的 AI 网关骨架，适合用于搭建长期运行的个人 AI、陪伴型 AI、聊天机器人网关或 Agent 服务。

目前公开版保留的方向包括：

- OpenAI 兼容 `/v1/chat/completions` 接口
- OpenAI-Compatible 上游模型接入
- 动态 system context 组装
- Prompt 扩展接口
- Function Calling / Tool Calling 扩展范式
- 后台任务与自主任务结构
- MiniApp / 管理页面挂载方式
- 私有 Overlay 分层思路

公开版不会预设 AI 必须叫什么，也不会预设使用者是谁、双方是什么关系。

---

## 2. 与私人完整版的关系

私人完整版长期用于实际个人场景，内部包含大量只属于原作者本人的内容，例如：

- 私人人格 Prompt
- 专属关系设定与称呼
- 私人聊天规则
- 原始 MiniApp UI / CSS / JavaScript
- 私人长期记忆与日记
- 设备、位置、健康、排班等生活数据
- 私人邮件联系人
- 家庭、宠物、世界观数据
- 私有 MCP / API 服务
- 私人工具实现
- Bot ID、群 ID、Token、Key 等配置

这些内容**不会进入公开仓库**。

本仓库不是私人仓库的镜像，也不会保持一比一文件对应。更准确地说，它是从私人项目中抽离出的公共工程层。

```text
私人完整版
├─ 网关核心
├─ 上下文系统
├─ 后台任务
├─ 工具系统
├─ 私人人格 / Prompt
├─ 私人 UI
├─ 私人生活数据
├─ 私有服务
└─ 个人定制逻辑

        ↓ 仅保留可公开部分

wang-guan-open
├─ 通用网关结构
├─ Context 扩展接口
├─ Prompt 示例
├─ Tool 扩展范式
├─ Background Task 示例
└─ MiniApp 挂载示例
```

---

## 3. 当前架构

公开版已经按私人项目的最新工程结构重新整理，而不是基于旧版本直接复制。

```text
容器
├─ main.py
│  └─ HTTP / OpenAI-Compatible 实时网关
└─ background_main.py
   └─ 独立后台任务进程
```

两个进程通过 `entrypoint.sh` 同时启动。任意一个退出时，容器会结束另一个进程，由部署平台统一重启，避免出现只剩半套服务还在运行的状态。

同时保留最新版工程中的几个通用设计：

- `bg_executor.py`：有限大小的共享线程池，避免 fire-and-forget 任务无限创建系统线程
- `context.py`：可注册的 Context Provider 机制
- `free_tools.py`：工具 Schema / Dispatch 聚合层
- `background_tasks.py`：后台协程注册入口
- `platforms/`：平台传输层的扩展边界

私人项目中的具体行为逻辑不会随这些结构一起公开。

---

## 4. OpenAI 兼容网关

公开版提供：

```text
POST /v1/chat/completions
```

可接入任意兼容 OpenAI Chat Completions 格式的上游模型。

基础环境变量：

```env
API_SECRET=change-me
LLM_BASE_URL=https://example.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

运行：

```bash
pip install -r requirements.txt
python main.py
```

默认监听：

```text
0.0.0.0:8000
```

---

## 5. Context Builder

`context.py` 提供 system context 的扩展入口。

最小写法：

```python
def build_context() -> str:
    return "Your system context here"
```

你可以自行加入：

- 人格配置
- 用户画像
- 长期记忆
- 对话摘要
- 时间与日历
- 数据库状态
- 自定义业务信息

私人完整版中的个人 Context 查询与注入逻辑不会公开。

建议把真正私密的数据存放在环境变量、私有数据库或独立私有配置层中。

---

## 6. Prompt

`prompts.py` 只提供泛化示例和模板写法。

不会公开原私人项目中的：

- 人格原文
- 专属称呼
- 双方关系设定
- 自由活动 Prompt
- 私人总结 / 日记 Prompt
- 私人行为规则

推荐使用占位符或环境变量：

```python
AI_NAME = os.environ.get("AI_NAME", "AI")
USER_NAME = os.environ.get("USER_NAME", "User")
```

不要把真实私人内容直接提交到公开仓库。

---

## 7. Tool 扩展方式

私人完整版拥有大量外部工具和服务接入，这些具体实现不会公开。

公开版只保留工具开发范式：

```python
def example_tool(text: str) -> str:
    return text

SCHEMAS = [{
    "type": "function",
    "function": {
        "name": "example_tool",
        "description": "Example tool",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    }
}]

DISPATCH = {
    "example_tool": lambda args: example_tool(args["text"])
}
```

再由 `free_tools.py` 统一聚合。

你可以按同一结构创建自己的：

```text
tools_weather.py
tools_search.py
tools_calendar.py
tools_memory.py
tools_xxx.py
```

---

## 8. Background Tasks

`background_main.py` 保留后台任务的基本组织形式，可用于：

- 定时总结
- 记忆整理
- 数据同步
- 定时检查
- Agent 自主任务
- 消息轮询

私人完整版中的具体自主行为、生活逻辑与私人自动化不会公开。

---

## 9. MiniApp / UI

私人完整版中的 MiniApp 是原作者长期自行设计和修改的私人 UI。

**原始 HTML、CSS、JavaScript、页面结构、组件和视觉方案均不属于本公开项目。**

因此公开仓库只保留一个最小挂载示例，用于说明如何通过网关提供自己的管理页面。

```text
miniapp/miniapp.html
```

请自行设计前端。

这不是缺失文件，也不是待补全功能，而是明确的公开边界。

---

## 10. 推荐的私人 Overlay 结构

建议把公共核心和私人层分开维护：

```text
wang-guan-open/        # 源码公开的公共核心

my-private-overlay/    # 你自己的私有仓库
├─ persona/
├─ prompts/
├─ ui/
├─ tools/
├─ integrations/
└─ private-config/
```

仓库中的 `PRIVATE_OVERLAY.example.md` 提供了一个简单示例。

这种结构可以避免未来分享代码时反复做隐私清理。

---

## 11. 许可协议

本项目采用 **PolyForm Noncommercial License 1.0.0**。

允许：

- 个人学习与研究
- 非商业部署
- 修改源码
- 制作非商业衍生版本
- 在遵守协议的前提下分发非商业版本

不允许：

- 将本项目或衍生版本收费售卖
- 将其作为付费产品的一部分提供
- 以本项目为基础提供收费 SaaS / 托管服务
- 其他以商业获利为目的的使用

需要商业授权，请先取得作者单独许可。

注意：由于协议限制商业用途，本项目属于 **source-available（源码公开）**，而不是 OSI 定义下的 Open Source Software。

完整法律文本以 `LICENSE` 为准。

---

## 12. 项目原则

这个仓库公开的是“怎么搭”，不是“把我的私人 AI 拿走”。

工程结构可以参考和二次开发，但原作者的人格、关系、UI、记忆、私人数据与服务边界不会随代码一并公开。
