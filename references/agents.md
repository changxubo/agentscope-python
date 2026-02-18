# Agent Types and Creation Reference

## Table of Contents
- [Built-in Agent Types](#built-in-agent-types)
- [ReActAgent](#reactagent)
- [DialogAgent](#dialogagent)
- [UserAgent](#useragent)
- [Custom Agents](#custom-agents)
- [Agent Configuration](#agent-configuration)

## Built-in Agent Types

AgentScope provides several built-in agent types:

| Agent Type | Description | Use Case |
|------------|-------------|----------|
| `ReActAgent` | Reasoning + Acting agent with tool support | Task automation, code execution |
| `DialogAgent` | Simple conversational agent | Chatbots, Q&A systems |
| `UserAgent` | Human-in-the-loop interface | Interactive applications |
| `TextToImageAgent` | Image generation agent | Visual content creation |
| `MultiModalAgent` | Handles text + images | Vision-language tasks |

## ReActAgent

The most powerful built-in agent that follows the ReAct (Reason + Act) paradigm.

### Basic Usage

```python
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.memory import InMemoryMemory
from agentscope.formatter import DashScopeChatFormatter
from agentscope.tool import Toolkit

# Create toolkit with tools
toolkit = Toolkit()
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(execute_shell_command)

# Create ReActAgent
agent = ReActAgent(
    name="Friday",
    sys_prompt="You are a helpful AI assistant with coding capabilities.",
    model=DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ["DASHSCOPE_API_KEY"],
        stream=True
    ),
    memory=InMemoryMemory(),
    formatter=DashScopeChatFormatter(),
    toolkit=toolkit,
    max_iters=10  # Maximum reasoning iterations
)

# Use the agent
response = await agent(Msg(name="user", content="Calculate fibonacci of 10", role="user"))
```

### ReActAgent Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Agent identifier |
| `sys_prompt` | str | System prompt for the agent |
| `model` | ModelWrapper | LLM model instance |
| `memory` | Memory | Memory for conversation history |
| `formatter` | Formatter | Message formatter for the model |
| `toolkit` | Toolkit | Collection of tools |
| `max_iters` | int | Maximum reasoning iterations (default: 10) |
| `verbose` | bool | Print reasoning steps (default: True) |

## DialogAgent

Simple agent for conversational interactions without tool use.

```python
from agentscope.agent import DialogAgent

agent = DialogAgent(
    name="ChatBot",
    sys_prompt="You are a friendly conversational assistant.",
    model=OpenAIChatModel(
        model_name="gpt-4o",
        api_key=os.environ["OPENAI_API_KEY"]
    ),
    memory=InMemoryMemory(),
    use_memory=True
)

# Simple conversation
msg = Msg(name="user", content="What's the weather today?", role="user")
response = await agent(msg)
```

## UserAgent

Agent representing human user input in multi-agent systems.

```python
from agentscope.agent import UserAgent

user = UserAgent(
    name="user",
    prompt="Please provide your input: "
)

# In a conversation loop
while True:
    msg = await agent(msg)
    msg = await user(msg)  # Gets input from human
    if msg.get("text_content") == "exit":
        break
```

## Custom Agents

Create custom agents by inheriting from `AgentBase`:

```python
from agentscope.agent import AgentBase
from agentscope.message import Msg

class MyCustomAgent(AgentBase):
    def __init__(self, name, model, **kwargs):
        super().__init__(name=name, **kwargs)
        self.model = model
        
    async def __call__(self, msg: Msg = None) -> Msg:
        """Process incoming message and return response."""
        # 1. Process input
        if msg is not None:
            self.memory.add(msg)
        
        # 2. Generate response using model
        messages = self.memory.get_memory()
        response = await self.model(messages)
        
        # 3. Create and return output message
        output = Msg(
            name=self.name,
            content=response.content,
            role="assistant"
        )
        self.memory.add(output)
        
        return output
```

### Custom Agent with Tools

```python
class ToolUsingAgent(AgentBase):
    def __init__(self, name, model, toolkit, **kwargs):
        super().__init__(name=name, **kwargs)
        self.model = model
        self.toolkit = toolkit
        
    async def __call__(self, msg: Msg = None) -> Msg:
        # Add to memory
        if msg:
            self.memory.add(msg)
        
        # Get model response with tool calls
        response = await self.model(
            self.memory.get_memory(),
            tools=self.toolkit.get_tools()
        )
        
        # Execute tool calls if present
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = await self.toolkit.execute(tool_call)
                # Add tool result to memory
                self.memory.add(Msg(
                    name="tool",
                    content=result,
                    role="tool"
                ))
            # Get final response
            response = await self.model(self.memory.get_memory())
        
        return Msg(name=self.name, content=response.content, role="assistant")
```

## Agent Configuration

### Using Configuration Dictionary

```python
from agentscope.agent import load_agent_from_config

config = {
    "class_type": "ReActAgent",
    "name": "assistant",
    "sys_prompt": "You are a helpful assistant.",
    "model": {
        "class_type": "DashScopeChatModel",
        "model_name": "qwen-max",
        "api_key": "${DASHSCOPE_API_KEY}"
    },
    "memory": {
        "class_type": "InMemoryMemory"
    },
    "toolkit": {
        "class_type": "Toolkit",
        "tools": ["execute_python_code", "execute_shell_command"]
    }
}

agent = load_agent_from_config(config)
```

### Model-Specific Formatters

Different models require different message formatters:

```python
from agentscope.formatter import (
    DashScopeChatFormatter,    # Qwen models
    OpenAIChatFormatter,        # GPT models
    AnthropicChatFormatter,     # Claude models
)

# Match formatter to model
agent = ReActAgent(
    name="assistant",
    model=OpenAIChatModel(...),
    formatter=OpenAIChatFormatter(),  # Match!
    ...
)
```

## Best Practices

1. **Always use async/await** when calling agents
2. **Match formatter to model** for correct message formatting
3. **Set appropriate max_iters** for ReActAgent to prevent infinite loops
4. **Use memory** for maintaining conversation context
5. **Register tools before** passing toolkit to agent
