# Wang Guan Open

`wang-guan-open` 是从我自己的私人 AI 网关项目中剥离出来的公开版本。

原项目长期用于个人 AI 陪伴、跨平台聊天、记忆、上下文同步、后台任务与工具调用，因此内部包含大量只属于我自己的内容：私人 UI、人格提示词、关系设定、专属称呼、生活数据、设备状态、个人记忆、私人 MCP/工具、服务地址与自动化逻辑等。

这些内容不会公开。

这个仓库保留的是项目中可以复用的工程结构、接口形式和扩展思路，方便其他人基于它搭建自己的版本，而不是复制我的私人 AI。

---

## 这个仓库是什么

它是一个可自行扩展的 AI 网关骨架，核心目标是把多个能力集中到一个统一服务中，例如：

- 提供 OpenAI 兼容的 `/v1/chat/completions` 接口
- 接入任意 OpenAI-Compatible LLM 服务
- 动态构建 system context
- 自定义人格与提示词
- 扩展 Function Calling / Tool Calling
- 增加后台定时任务或自主任务
- 挂载自己的管理页面 / MiniApp
- 继续扩展数据库、记忆、机器人平台等功能

公开版不会预设“AI 应该是谁”，也不会预设“用户是谁”。

你可以把它改造成自己的 AI 助手、陪伴型 AI、聊天机器人网关或其他长期运行的 Agent 服务。

---

## 与私人完整版的关系

我实际使用的版本位于另一个私人仓库中，并持续维护。

公开仓库不是私人仓库的镜像，也不会保持文件一比一对应。

两者关系更接近：

```text
私人完整版
├─ 通用网关架构
├─ 上下文系统
├─ 后台任务系统
├─ 工具系统
├─ 私人人格 / Prompt
├─ 私人 UI
├─ 私人生活数据
├─ 私人服务与 MCP
└─ 大量个人定制逻辑

        ↓ 剥离所有私人内容

wang-guan-open
├─ 通用网关骨架
├─ Context 扩展接口
├─ Prompt 示例
├─ Tool 扩展范式
├─ Background Task 示例
└─ MiniApp 挂载示例
```

我以前还维护过一版用于整理项目结构的仓库 `tiantian-wg`。那一版更接近当时私人项目的完整代码结构，也留下了不少个人定制内容。

这次的 `wang-guan-open` 采取更严格的边界：只公开可以复用的实现思路，不继续公开我的私人 AI 本身。

---

## 为什么没有直接把原仓库公开

因为这个项目并不是一开始按照“开源软件”设计的。

它在长期使用过程中逐渐混入了大量个人生活信息和专属逻辑。如果直接把原仓库删几个 Key 就公开，很容易留下：

- 私人名字与称呼
- AI 与我的关系设定
- 完整人格 Prompt
- 私人聊天规则
- 私人 UI 设计
- 个人设备、位置、排班、健康等数据结构
- 私人记忆与日记逻辑
- 私人邮箱联系人
- 私人 MCP / API 服务
- 私人机器人 ID、群 ID、频道配置
- 开发过程中曾出现过的历史配置

所以这个仓库不是通过“复制后删除”生成，而是重新建立了一套干净的公开骨架。

这也意味着：原私人仓库的 Git 历史不会出现在这里。

---

## 已保留的内容

当前公开版主要保留以下通用部分。

### OpenAI 兼容网关

提供：

```text
POST /v1/chat/completions
```

可接入 OpenAI-Compatible 上游模型。

主要配置：

```env
API_SECRET=change-me
LLM_BASE_URL=https://example.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

---

### Context Builder

`context.py` 提供上下文组装入口。

公开版只提供通用范式，例如：

```python
def build_context() -> str:
    return "Your system context here"
```

你可以自行接入：

- 数据库
- 用户画像
- 长期记忆
- 对话摘要
- 时间信息
- 日历
- 设备状态
- 自定义业务数据

私人完整版中的个人 Context 读取逻辑不会公开。

---

### Prompt

`prompts.py` 中只保留泛化示例。

不会公开：

- 我的 AI 人格原文
- 私人关系设定
- 专属称呼
- 自由活动 Prompt
- 私人日记 / 总结 Prompt
- 我的行为偏好与互动规则

建议把自己的 Prompt 放在：

- 环境变量
- 私有数据库
- 私有配置文件
- 私有 Overlay 仓库

而不是直接硬编码到公开仓库。

---

### Tool 扩展方式

私人完整版拥有较多工具与外部服务接入，这些实现不在公开范围内。

公开版只保留工具的标准写法。

一个工具模块通常包含三部分：

```python
def example_tool(text: str) -> str:
    return text

SCHEMAS = [
    {
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
    }
]

DISPATCH = {
    "example_tool": lambda args: example_tool(args["text"])
}
```

再由 `free_tools.py` 统一聚合。

你可以按照这个模式自行创建：

```text
tools_weather.py
tools_search.py
tools_calendar.py
tools_memory.py
tools_xxx.py
```

具体调用什么服务，由你自己决定。

---

### Background Tasks

`background_main.py` 保留后台任务的基本组织方式。

可以用于：

- 定时总结
- 记忆整理
- 定时检查
- Agent 自主任务
- 数据同步
- 消息轮询

私人完整版中的具体自主行为逻辑不会公开。

---

## MiniApp / UI

这里需要单独说明。

私人完整版拥有我自己长期设计和修改的 MiniApp UI，包括页面结构、组件、交互和视觉方案。

**这些 UI 不属于本开源项目的一部分。**

因此：

```text
miniapp/miniapp.html
```

只保留一个最小占位示例，用于说明如何通过网关挂载自己的页面。

请自行设计自己的前端。

这不是缺文件，也不是待补全功能，而是有意不公开。

---

## 明确不会公开的内容

包括但不限于：

- 原始 MiniApp HTML / CSS / JavaScript
- 原始视觉设计与组件
- 私人人格 Prompt
- AI 与我的私人关系设定
- 私人称呼、名字、身份锚点
- 私人聊天历史
- 私人长期记忆
- 私人日记
- 私人生活数据
- 设备状态 / 定位 / 健康 / 排班等个人数据逻辑
- 私人邮件联系人
- 私人家庭 / 宠物 / 世界观数据
- 私人自由活动规则
- 私有 MCP 服务
- 私人工具实现
- Token / API Key / Bot ID / 群 ID
- 私有数据库内容
- 仅服务于我个人使用习惯的自动化逻辑

如果公开版中出现类似能力，只会提供通用接口或示例写法。

---

## 推荐的二开方式

如果你准备长期维护自己的版本，建议不要直接把私人内容写回这个公开仓库。

比较推荐：

```text
wang-guan-open        # 公共核心

my-private-config     # 你自己的私有层
├─ persona
├─ prompts
├─ ui
├─ tools
├─ integrations
└─ private config
```

也可以通过环境变量、数据库和挂载目录实现同样的隔离。

仓库里提供了：

```text
PRIVATE_OVERLAY.example.md
```

用于说明这种拆分方式。

---

## 快速运行

```bash
cp .env.example .env
```

填写自己的模型配置后：

```bash
pip install -r requirements.txt
python main.py
```

默认监听：

```text
0.0.0.0:8000
```

然后使用：

```text
POST /v1/chat/completions
```

即可调用。

---

## 项目原则

这个仓库公开的是“怎么搭”，不是“把我的 AI 拿走”。

代码结构和工程经验可以复用，但人格、关系、UI、记忆与私人生活数据应该属于各自的使用者。

如果你基于这个项目二开，建议也把公共核心和私人配置分开维护。以后想开源、迁移或分享时，会省掉很多麻烦。

---

## License

MIT License。详见 `LICENSE`。
