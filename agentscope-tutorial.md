# AgentScope: A Complete Developer's Guide

## Introduction

AgentScope is an open-source, production-ready multi-agent platform developed by Alibaba for building, orchestrating, and deploying LLM-powered agent systems. It emphasizes developer experience with concise APIs while providing enterprise-grade features like distributed execution, fault tolerance, and visual programming tools.

**GitHub**: [https://github.com/agentscope-ai/agentscope](https://github.com/agentscope-ai/agentscope)  
**Documentation**: [https://doc.agentscope.io](https://doc.agentscope.io)  
**PyPI**: `pip install agentscope`

---

## Key Features at a Glance

| Feature | Description |
|---------|-------------|
| **ReAct Agent** | Built-in Reasoning + Acting paradigm for autonomous task execution |
| **Zero-Code UI** | Drag-and-drop workstation for visual agent design |
| **Message Hub** | Flexible multi-agent orchestration via explicit message passing |
| **MCP Support** | Native integration with Model Context Protocol servers |
| **A2A Protocol** | Agent-to-Agent communication standard support |
| **Distributed** | Actor-based framework for seamless local→distributed deployment |
| **Fault Tolerance** | Auto-retry, rule-based correction, configurable error handling |
| **Memory Systems** | Short-term, long-term (Mem0, ReMe), and tool memory |
| **Planning** | Built-in plan management with subtask decomposition |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interaction Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Annotated    │  │ Web UI       │  │ Drag-and-Drop    │  │
│  │ Terminal     │  │ Monitoring   │  │ Workstation      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Agent Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ ReActAgent   │  │ UserAgent    │  │ Custom Agents    │  │
│  │ (Reason+Act) │  │ (Human Loop) │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Communication Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ MsgHub       │  │ Pipeline     │  │ Message Center   │  │
│  │ (Broadcast)  │  │ (Workflow)   │  │ (Routing)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Model Wrapper│  │ Toolkit/MCP  │  │ Memory (ReMe)    │  │
│  │ (LLM APIs)   │  │ (Tools)      │  │ (Persistence)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Distribution Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Actor-Based Distributed Backend (Ray-powered)         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start: Your First Agent

### Installation

```bash
pip install agentscope
```

### Basic ReAct Agent Example

```python
import asyncio
import os
from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, execute_python_code, execute_shell_command

async def main():
    # Create toolkit with built-in tools
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(execute_shell_command)
    
    # Create ReAct Agent
    agent = ReActAgent(
        name="Friday",
        sys_prompt="You're a helpful assistant named Friday. Use tools when needed.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit
    )
    
    # Create User Agent for human-in-the-loop
    user = UserAgent(name="user")
    
    # Main conversation loop
    msg = None
    while True:
        msg = await agent(msg)
        msg = await user(msg)
        if msg.get_text_content == "exit":
            break

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Core Concepts Deep Dive

### 1. Messages: The Communication Unit

Messages are the fundamental unit of communication between agents:

```python
from agentscope.message import Msg

# Basic message
msg = Msg(
    name="user",
    content="Analyze the market trends for AI agents",
    role="user"
)

# Multi-modal message (with URLs)
multimodal_msg = Msg(
    name="user",
    content="What's in this image?",
    urls=["https://example.com/image.png"],
    role="user"
)
```

### 2. MsgHub: Multi-Agent Broadcasting

MsgHub enables group conversations where messages from any participant are automatically broadcast to all others:

```python
from agentscope.hub import MsgHub
from agentscope.message import Msg

async def group_conversation():
    # Create message hub with participants
    async with MsgHub(
        participants=[alice, bob, charlie],
        announcement=Msg(
            "user",
            "Each agent should introduce themselves!",
            "user"
        ),
    ) as hub:
        # All responses auto-broadcast to other participants
        await alice()  # Bob and Charlie receive this
        await bob()    # Alice and Charlie receive this
        await charlie() # Alice and Bob receive this
```

**MsgHub Features:**
- **Auto-broadcast**: Messages automatically shared with all participants
- **Dynamic membership**: Add/remove agents during runtime
- **Manual broadcast control**: Toggle auto-broadcast on/off

```python
# Dynamic membership
hub.register(bob)      # Add Bob to conversation
hub.unregister(charlie) # Remove Charlie

# Manual broadcast control
hub.disable_auto_broadcast()  # Turn off auto-broadcast
hub.broadcast(alice_reply)    # Manually broadcast specific message
hub.enable_auto_broadcast()   # Turn on auto-broadcast
```

### 3. Pipeline: Workflow Orchestration

AgentScope provides high-level pipeline abstractions for common workflow patterns:

#### Sequential Pipeline

```python
from agentscope.pipeline import sequential_pipeline

# Execute agents in order, passing output from one to next
result = await sequential_pipeline(
    agents=[researcher, analyzer, writer],
    msg=Msg("user", "Research AI agent frameworks", "user")
)
```

#### Fan-out Pipeline (Parallel Execution)

```python
from agentscope.pipeline import fanout_pipeline, FanoutPipeline

# Execute agents in parallel with same input
results = await fanout_pipeline(
    agents=[translator_en, translator_fr, translator_de],
    msg=Msg("user", "Translate: Hello World", "user"),
    enable_gather=True  # Collect results into list
)

# Or create reusable pipeline object
pipeline = FanoutPipeline(agents=[agent1, agent2, agent3])
results1 = await pipeline(msg=input1)
results2 = await pipeline(msg=input2)  # Reuse
```

### 4. Planning: Task Decomposition

AgentScope provides built-in planning capabilities with subtask management:

```python
from agentscope.plan import Plan, Subtask

# Create a structured plan
plan = Plan(
    goal="Conduct comprehensive research on LLM agents",
    subtasks=[
        Subtask(
            title="Literature Review",
            content="Survey academic papers on LLM agents"
        ),
        Subtask(
            title="Industry Analysis",
            content="Analyze commercial agent frameworks"
        ),
        Subtask(
            title="Future Trends",
            content="Identify emerging trends and predictions"
        ),
    ]
)

# Agent-managed plan execution
# The agent can use plan management tools:
# - create_plan, view_subtasks, revise_current_plan
# - update_subtask_state, finish_subtask, finish_plan
# - view_historical_plans, recover_historical_plan
```

---

## Tool Integration

### Built-in Tools

```python
from agentscope.tool import Toolkit, execute_python_code, execute_shell_command

toolkit = Toolkit()
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(execute_shell_command)
```

### Custom Tool Functions

```python
from agentscope.tool import Toolkit

def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        Search results as formatted string
    """
    # Your implementation here
    return f"Results for: {query}"

toolkit = Toolkit()
toolkit.register_tool_function(search_web)
```

### MCP (Model Context Protocol) Integration

AgentScope natively supports MCP servers for extended tool ecosystems:

```python
from agentscope.tool import Toolkit
from agentscope.tool.mcp import McpClientBuilder

async def mcp_integration():
    toolkit = Toolkit()
    
    # Connect to MCP server (StdIO transport)
    client = await McpClientBuilder.create("map_services") \
        .stdio("python", ["-m", "mcp_server"]) \
        .build()
    
    # Register all tools from MCP server
    await toolkit.register_mcp_client(
        client,
        group_name="map_services"  # Optional grouping
    )
    
    # Now agent can use MCP tools
    agent = ReActAgent(
        name="MapAgent",
        sys_prompt="You help with location queries",
        toolkit=toolkit,
        # ... other params
    )
```

**MCP Transport Types:**
- **StdIO**: Local MCP server via standard input/output
- **HTTP**: HTTP-based MCP server
- **SSE**: Server-Sent Events transport

---

## Memory Management

### Short-term Memory (Session-based)

```python
from agentscope.memory import InMemoryMemory

# In-memory conversation history
memory = InMemoryMemory()
```

### Long-term Memory with ReMe

ReMe is AgentScope's modular memory management kit for cross-session persistence:

```python
from reme_ai import ReMeApp

async def memory_example():
    async with ReMeApp(
        "llm.default.model_name=qwen-max",
        "embedding_model.default.model_name=text-embedding-v4",
        "vector_store.default.backend=memory"
    ) as app:
        
        # Store experience from trajectories
        result = await app.async_execute(
            name="summary_task_memory",
            workspace_id="my_workspace",
            trajectories={
                "messages": [
                    {"role": "user", "content": "Help me create a project plan"},
                    {"role": "assistant", "content": "..."}
                ],
                "score": 1.0
            }
        )
        
        # Retrieve relevant memories
        result = await app.async_execute(
            name="retrieve_task_memory",
            workspace_id="my_workspace",
            query="How to manage project progress?",
            top_k=5
        )
```

### Memory Integration with Agent

```python
from agentscope.memory import LongTermMemoryMode
from agentscope.memory.reme import ReMeLongTermMemory

# Configure agent with long-term memory
agent = ReActAgent(
    name="Assistant",
    long_term_memory_mode=LongTermMemoryMode.ENABLED,
    long_term_memory=ReMeLongTermMemory(
        api_key="your-reme-api-key",
        workspace_id="user_workspace"
    ),
    # ... other params
)
```

---

## Fault Tolerance & Reliability

AgentScope provides configurable fault tolerance:

```python
from agentscope.model import DashScopeChatModel

model = DashScopeChatModel(
    model_name="qwen-max",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    
    # Fault tolerance configuration
    max_retries=3,           # Maximum retry attempts
    parse_func=None,         # Custom response parser
    fault_handler=None,      # Custom error handler
)
```

**Fault Tolerance Features:**

| Mechanism | Description |
|-----------|-------------|
| **Auto-retry** | Automatically retry on transient errors (network, rate limits) |
| **Rule-based correction** | Built-in rules handle common formatting errors |
| **Custom handlers** | Define your own parsing and error recovery logic |
| **Model-resolvable errors** | Let LLM self-correct verbose or malformed outputs |

---

## Distributed Deployment

AgentScope uses an actor-based distributed backend for seamless scaling:

### Local to Distributed Conversion

```python
from agentscope.distributed import distribute

# Define your agent locally
local_agent = ReActAgent(
    name="DistributedAgent",
    # ... configuration
)

# Convert to distributed deployment
distributed_agent = distribute(local_agent)

# Use exactly the same way - framework handles distribution
result = await distributed_agent(msg)
```

**Benefits of Actor-Based Distribution:**
- Same code works locally and distributed
- Automatic parallel optimization
- Transparent message passing between distributed agents
- Built on Ray for reliability

---

## Comparison with Other Frameworks

| Framework | Approach | Best For |
|-----------|----------|----------|
| **AgentScope** | Message-passing, Actor-based | Multi-agent orchestration, distributed systems |
| **LangGraph** | Graph-based state machine | Complex workflows, conditional branching |
| **CrewAI** | Role-based teams | Collaborative tasks with specialized roles |
| **AutoGen** | Conversational patterns | Human-in-the-loop, interactive systems |
| **SmolAgents** | Code-driven | Dynamic planning, code generation |

**When to Choose AgentScope:**
- ✅ Need distributed multi-agent systems
- ✅ Want zero-code visual development option
- ✅ Require MCP/A2A protocol support
- ✅ Building production-grade applications
- ✅ Need built-in memory management (ReMe)
- ✅ Want fault-tolerant agent execution

---

## Complete Example: Multi-Agent Research Team

```python
import asyncio
import os
from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import DashScopeChatModel, OpenAIChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, execute_python_code
from agentscope.hub import MsgHub
from agentscope.pipeline import sequential_pipeline, fanout_pipeline
from agentscope.message import Msg

async def research_team():
    # Shared toolkit
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    
    # Create specialized agents
    researcher = ReActAgent(
        name="Researcher",
        sys_prompt="You are a research specialist. Gather comprehensive information.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit
    )
    
    analyzer = ReActAgent(
        name="Analyzer",
        sys_prompt="You are a data analyst. Identify patterns and insights.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
    )
    
    writer = ReActAgent(
        name="Writer",
        sys_prompt="You are a technical writer. Create clear, engaging content.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
    )
    
    # Sequential workflow
    print("=== Sequential Research Workflow ===")
    result = await sequential_pipeline(
        agents=[researcher, analyzer, writer],
        msg=Msg("user", "Research and report on agentic AI trends in 2026", "user")
    )
    print(result.get_text_content())
    
    # Group discussion via MsgHub
    print("\n=== Group Discussion ===")
    async with MsgHub(
        participants=[researcher, analyzer, writer],
        announcement=Msg("user", "Discuss: What is the biggest challenge for AI agents?", "user"),
    ) as hub:
        await researcher()
        await analyzer()
        await writer()

if __name__ == "__main__":
    asyncio.run(research_team())
```

---

## Three-Stage Application Pattern

AgentScope recommends a structured pattern for production applications:

### Stage 1: Initialize

```python
from agentscope.app import AgentApp

async def init():
    """Initialize resources, load models, setup connections"""
    app = AgentApp()
    await app.setup()
    return app
```

### Stage 2: Query/Process

```python
async def query(app, user_input):
    """Handle user requests"""
    result = await app.agent(Msg("user", user_input, "user"))
    return result
```

### Stage 3: Shutdown

```python
async def shutdown(app):
    """Cleanup resources"""
    await app.teardown()
```

---

## Supported LLM Providers

| Provider | Model Wrapper | Example Models |
|----------|--------------|----------------|
| Alibaba DashScope | `DashScopeChatModel` | qwen-max, qwen-plus |
| OpenAI | `OpenAIChatModel` | gpt-4, gpt-3.5-turbo |
| Anthropic | `AnthropicChatModel` | claude-3-opus |
| Custom | `CustomModel` | Any OpenAI-compatible API |

---

## Resources

- **GitHub Repository**: [https://github.com/agentscope-ai/agentscope](https://github.com/agentscope-ai/agentscope)
- **Official Documentation**: [https://doc.agentscope.io](https://doc.agentscope.io)
- **AgentScope Java**: [https://java.agentscope.io](https://java.agentscope.io)
- **ReMe Memory**: [https://github.com/agentscope-ai/ReMe](https://github.com/agentscope-ai/ReMe)
- **PyPI Package**: [https://pypi.org/project/agentscope](https://pypi.org/project/agentscope)

---

## Summary

AgentScope stands out as a production-ready multi-agent framework with:

1. **Developer-First Design**: Concise APIs that let you build agents in minutes
2. **Enterprise Features**: Distributed execution, fault tolerance, monitoring
3. **Zero-Code Option**: Drag-and-drop UI for rapid prototyping
4. **Protocol Support**: Native MCP and A2A integration
5. **Complete Ecosystem**: Memory (ReMe), planning, tools, and visual development

Whether you're building a simple conversational agent or a complex distributed multi-agent system, AgentScope provides the abstractions and infrastructure to scale from prototype to production.

---

*Last updated: February 2026*
