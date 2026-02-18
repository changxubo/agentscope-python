# AgentScope Skill

## What we built:

Agent Skill to build production-ready multi-agent applications with Alibaba's AgentScope framework.

## How to install:

```bash
npx skills add https://github.com/changxubo/agentscope-python --skill agentscope-python
```
## Sample usage:


```python
import asyncio
import os
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, execute_python_code

async def build_agent():
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    
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

## Core Patterns

### Pattern 1: Simple Conversational Agent

**Use Case**: Chatbots, Q&A systems, simple assistants

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

**Reference**: See `references/agents.md` for all agent types.

### Pattern 2: Tool-Using Agent (ReAct)

**Use Case**: Task automation, code execution, web browsing

```python
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit, execute_python_code, execute_shell_command

toolkit = Toolkit()
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(execute_shell_command)

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

**Reference**: See `references/tools-mcp.md` for custom tools and MCP integration.

### Pattern 3: Multi-Agent Pipeline

**Use Case**: Sequential workflows, parallel processing

```python
from agentscope.pipeline import sequential_pipeline, fanout_pipeline

# Sequential: agent1 -> agent2 -> agent3
result = await sequential_pipeline(
    agents=[researcher, analyzer, writer],
    msg=initial_msg
)

# Parallel: all agents process same input
results = await fanout_pipeline(
    agents=[sentiment_agent, entity_agent, summary_agent],
    msg=input_msg
)
```

**Reference**: See `references/pipelines.md` for orchestration patterns.

### Pattern 4: Multi-Agent Conversation (MsgHub)

**Use Case**: Group discussions, collaborative agents

```python
from agentscope.hub import MsgHub

async with MsgHub(
    participants=[agent1, agent2, agent3],
    announcement=Msg("user", "Discuss the topic...", "user")
) as hub:
    await agent1()  # Broadcasts to others
    await agent2()  # Broadcasts to others
    await agent3()  # Broadcasts to others
```

### Pattern 5: Custom Agent

**Use Case**: Specialized behavior, custom logic

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

**Reference**: See `references/agents.md` for custom agent patterns.

## Model Configuration

### Supported Providers

```python
from agentscope.model import (
    DashScopeChatModel,   # Qwen models
    OpenAIChatModel,       # GPT models
    AnthropicChatModel,    # Claude models
)

# Match formatter to model
from agentscope.formatter import (
    DashScopeChatFormatter,
    OpenAIChatFormatter,
    AnthropicChatFormatter,
)

# Example: DashScope (Qwen)
agent = ReActAgent(
    model=DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ["DASHSCOPE_API_KEY"],
        stream=True
    ),
    formatter=DashScopeChatFormatter(),  # Match!
    ...
)
```

**Reference**: See `references/api_reference.md` for all model wrappers.

## Memory Systems

### Short-Term (Conversation History)

```python
from agentscope.memory import InMemoryMemory

memory = InMemoryMemory(
    max_messages=100,    # Limit by count
    summarization=True   # Auto-summarize old messages
)
```

### Long-Term (Cross-Session)

```python
from agentscope.memory import ReMeMemory

ltm = ReMeMemory(
    storage_path="./memory_store",
    embedding_model="text-embedding-v2"
)

# Search memories
results = await ltm.search(
    query="What did we discuss about Python?",
    top_k=5
)
```

**Reference**: See `references/memory.md` for memory patterns.

## MCP Integration

Connect to Model Context Protocol servers for extended tool ecosystems:

```python
from agentscope.tool import MCPToolkit

# StdIO transport (local server)
mcp_toolkit = MCPToolkit(
    server_name="filesystem",
    transport="stdio",
    command="python",
    args=["mcp_server.py"]
)

await mcp_toolkit.initialize()
tools = await mcp_toolkit.list_tools()

# Use with agent
agent = ReActAgent(name="agent", toolkit=mcp_toolkit, ...)
```

**Reference**: See `references/tools-mcp.md` for MCP patterns.

## Distributed Deployment

Convert local agents to distributed deployment:

```python
from agentscope.agent import to_dist_agent
import ray

ray.init(address="auto")  # Connect to cluster

local_agent = ReActAgent(name="worker", ...)
distributed_agent = to_dist_agent(local_agent)

# Use identically - framework handles distribution
result = await distributed_agent(msg)
```

**Reference**: See `references/distributed.md` for deployment patterns.

## Three-Stage Application Pattern

Production applications follow this structure:

```python
from agentscope.app import AgentApp

class MyApp(AgentApp):
    async def init(self):
        """Stage 1: Initialize resources"""
        self.agent = ReActAgent(...)
        self.toolkit = Toolkit()
        
    async def query(self, user_input: str):
        """Stage 2: Process requests"""
        msg = Msg(name="user", content=user_input, role="user")
        return await self.agent(msg)
        
    async def shutdown(self):
        """Stage 3: Cleanup resources"""
        await self.cleanup()
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/changxubo/agentscope-python/issues)
- **Discussions:** [GitHub Discussions](https://github.com/changxubo/agentscope-python/discussions)
- **Repository:** [github.com/changxubo/agentscope-python](https://github.com/changxubo/agentscope-python)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=changxubo/agentscope-python&type=date&legend=top-left)](https://www.star-history.com/#changxubo/agentscope-python&type=date&legend=top-left)

---