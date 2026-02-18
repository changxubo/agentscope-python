# AgentScope Architecture Reference

## Table of Contents
- [Layered Architecture](#layered-architecture)
- [Core Components](#core-components)
- [Message Flow](#message-flow)
- [Three-Stage Application Pattern](#three-stage-application-pattern)

## Layered Architecture

AgentScope follows a four-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│         (AgentApp, Workflows, User Interfaces)               │
├─────────────────────────────────────────────────────────────┤
│                    Agent Layer                               │
│    (ReActAgent, DialogAgent, UserAgent, Custom Agents)       │
├─────────────────────────────────────────────────────────────┤
│                    Communication Layer                       │
│        (MsgHub, Messages, Pipelines, Planning)               │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  (Model Wrappers, Memory, Tools, MCP, Fault Tolerance)       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Message (Msg)
The fundamental unit of communication between agents.

```python
from agentscope.message import Msg

# Basic message
msg = Msg(
    name="assistant",
    content="Hello, how can I help?",
    role="assistant"  # "system", "user", "assistant"
)

# Multi-modal message
msg = Msg(
    name="user",
    content=[
        {"type": "text", "text": "Analyze this image"},
        {"type": "image_url", "image_url": {"url": "path/to/image.png"}}
    ]
)

# Access message content
text = msg.content  # Get content
text = msg.text_content  # Get text-only content (extracts from multi-modal)
```

### 2. MsgHub (Message Center)
Central hub for message broadcasting and routing in multi-agent systems.

```python
from agentscope.hub import MsgHub

# Create a message hub
hub = MsgHub(name="team_hub")

# Register agents (automatically done when agent is created with hub)
hub.register(agent)

# Broadcast message to all agents in hub
hub.broadcast(msg)

# Manual routing to specific agent
hub.route_to(msg, target_agent_name)

# Get message history
history = hub.get_history()
```

### 3. Memory
AgentScope supports pluggable memory systems.

```python
from agentscope.memory import InMemoryMemory, TemporaryMemory

# In-memory conversation history
memory = InMemoryMemory()

# Temporary memory (cleared after each session)
memory = TemporaryMemory()

# Add message to memory
memory.add(msg)

# Get conversation history
history = memory.get_memory()

# Clear memory
memory.clear()
```

### 4. Model Wrappers
Unified interface for different LLM providers.

```python
from agentscope.model import (
    DashScopeChatModel,      # Alibaba's Qwen models
    OpenAIChatModel,          # OpenAI GPT models
    AnthropicChatModel,       # Claude models
    GeminiChatModel,          # Google Gemini
    ZhipuAIChatModel,         # ZhipuAI GLM models
)

# DashScope (Qwen)
model = DashScopeChatModel(
    model_name="qwen-max",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    stream=True
)

# OpenAI
model = OpenAIChatModel(
    model_name="gpt-4o",
    api_key=os.environ["OPENAI_API_KEY"],
    stream=True
)

# Anthropic Claude
model = AnthropicChatModel(
    model_name="claude-sonnet-4-20250514",
    api_key=os.environ["ANTHROPIC_API_KEY"],
    stream=True
)
```

## Message Flow

### Agent-to-Agent Communication
Agents communicate through explicit message passing:

```python
from agentscope.agent import DialogAgent

agent1 = DialogAgent(name="Alice", ...)
agent2 = DialogAgent(name="Bob", ...)

# Agent1 sends message to Agent2
msg = Msg(name="Alice", content="Hello Bob!", role="assistant")
response = await agent2(msg)  # Agent2 processes and responds
```

### Broadcasting via MsgHub
Multiple agents can communicate through a central hub:

```python
# Agents in same hub receive broadcast messages
hub = MsgHub(name="team")

agent1 = DialogAgent(name="agent1", hub=hub, ...)
agent2 = DialogAgent(name="agent2", hub=hub, ...)

# Broadcast from agent1 to all others
msg = Msg(name="agent1", content="Team update!", role="assistant")
hub.broadcast(msg)
```

## Three-Stage Application Pattern

AgentScope applications follow a consistent three-stage pattern:

```python
from agentscope.app import AgentApp

class MyAgentApp(AgentApp):
    def __init__(self):
        super().__init__(name="my_app")
        
    async def init(self):
        """Stage 1: Initialize resources"""
        # Setup agents, tools, memory
        self.agent = ReActAgent(...)
        self.toolkit = Toolkit()
        
    async def query(self, user_input: str):
        """Stage 2: Process user queries"""
        # Handle user interaction
        msg = Msg(name="user", content=user_input, role="user")
        response = await self.agent(msg)
        return response.content
        
    async def shutdown(self):
        """Stage 3: Cleanup resources"""
        # Close connections, save state
        await self.cleanup()

# Usage
app = MyAgentApp()
await app.init()
response = await app.query("Hello!")
await app.shutdown()
```

## Key Design Principles

1. **Message-Driven**: All agent interactions happen through explicit messages
2. **Asynchronous**: Built on async/await for concurrent operations
3. **Modular**: Components are pluggable and interchangeable
4. **Fault-Tolerant**: Built-in retry and error handling mechanisms
5. **Distributed-Ready**: Actor-based architecture for scaling
