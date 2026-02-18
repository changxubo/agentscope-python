# Memory Management Reference

## Table of Contents
- [Memory Types Overview](#memory-types-overview)
- [Short-Term Memory](#short-term-memory)
- [Long-Term Memory](#long-term-memory)
- [ReMe Memory System](#reme-memory-system)
- [Mem0 Integration](#mem0-integration)
- [Memory Best Practices](#memory-best-practices)

## Memory Types Overview

AgentScope supports two primary memory types:

| Type | Purpose | Persistence | Backend |
|------|---------|-------------|---------|
| **Short-term** | Conversation history | Session-based | `InMemoryMemory`, `TemporaryMemory` |
| **Long-term** | User preferences, facts | Cross-session | `ReMe`, `Mem0` |

## Short-Term Memory

### InMemoryMemory

Standard memory for maintaining conversation history:

```python
from agentscope.memory import InMemoryMemory

memory = InMemoryMemory()

# Add messages
memory.add(Msg(name="user", content="Hello", role="user"))
memory.add(Msg(name="assistant", content="Hi!", role="assistant"))

# Get history
history = memory.get_memory()
# Returns: List[Msg]

# Clear memory
memory.clear()
```

### TemporaryMemory

Memory that's cleared after each session:

```python
from agentscope.memory import TemporaryMemory

memory = TemporaryMemory()

# Automatically cleared when agent restarts
# Useful for one-off conversations
```

### Memory with Limits

```python
from agentscope.memory import InMemoryMemory

memory = InMemoryMemory(
    max_messages=50,      # Keep last 50 messages
    max_tokens=4000,      # Or limit by tokens
    summarization=True    # Auto-summarize old messages
)
```

## Long-Term Memory

### Overview

Long-term memory enables agents to:
- Remember user preferences across sessions
- Store and retrieve facts and knowledge
- Learn from past interactions

### Configuration

```python
from agentscope.memory import LongTermMemory

# Basic configuration
ltm = LongTermMemory(
    backend="reme",  # or "mem0"
    config={
        "storage_path": "./memory_store",
        "embedding_model": "text-embedding-ada-002"
    }
)
```

## ReMe Memory System

ReMe is AgentScope's built-in memory management system for agents.

### Features

- **Memory Extraction**: Extract important information from conversations
- **Memory Reuse**: Share memories across agents and sessions
- **Experience Summarization**: Learn from execution trajectories
- **Semantic Search**: Retrieve relevant memories by similarity

### Basic Usage

```python
from agentscope.memory import ReMeMemory

# Initialize ReMe memory
memory = ReMeMemory(
    storage_path="./reme_store",
    embedding_model="dashscope/text-embedding-v2",
    api_key=os.environ["DASHSCOPE_API_KEY"]
)

# Add memory
await memory.add_memory(
    content="User prefers Python over JavaScript",
    metadata={"user_id": "user_123", "type": "preference"}
)

# Search memories
results = await memory.search(
    query="What programming language does user prefer?",
    top_k=5
)

# Extract from conversation
await memory.extract_from_conversation(
    messages=conversation_history,
    user_id="user_123"
)
```

### Experience Summarization

Learn from agent execution trajectories:

```python
from agentscope.memory import ReMeMemory

memory = ReMeMemory(...)

# After agent execution
trajectory = [
    Msg(name="user", content="Fix the bug in main.py", role="user"),
    Msg(name="agent", content="Reading main.py...", role="assistant"),
    Msg(name="tool", content="def main(): ...", role="tool"),
    Msg(name="agent", content="Found the bug on line 10", role="assistant"),
    # ... more messages
]

# Extract experience
experience = await memory.summarize_experience(
    trajectory=trajectory,
    task_type="bug_fixing"
)

# Store for future reference
await memory.store_experience(experience)
```

### Memory Retrieval

```python
# Semantic search for relevant memories
relevant_memories = await memory.retrieve(
    query="How did we handle the database issue?",
    top_k=3,
    threshold=0.7  # Similarity threshold
)

# Each result includes:
# - content: The memory text
# - score: Similarity score
# - metadata: Associated metadata
```

## Mem0 Integration

AgentScope also supports Mem0 as a long-term memory backend.

### Setup

```python
from agentscope.memory import Mem0Memory

memory = Mem0Memory(
    api_key=os.environ["MEM0_API_KEY"],
    user_id="user_123"
)
```

### Usage

```python
# Add memory
await memory.add(
    messages=[
        {"role": "user", "content": "I work at ACME Corp"},
        {"role": "assistant", "content": "I'll remember that you work at ACME Corp"}
    ]
)

# Search memories
results = await memory.search(
    query="Where does the user work?",
    top_k=5
)

# Get all memories
all_memories = await memory.get_all()

# Delete memory
await memory.delete(memory_id="mem_xxx")
```

### Mem0 with Agent

```python
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory, Mem0Memory

# Combined memory: short-term + long-term
agent = ReActAgent(
    name="assistant",
    model=model,
    memory=InMemoryMemory(),      # Conversation history
    long_term_memory=Mem0Memory(  # Persistent knowledge
        api_key=os.environ["MEM0_API_KEY"],
        user_id="user_123"
    ),
    ...
)
```

## Memory Best Practices

### 1. Choose the Right Memory Type

```python
# For stateless chatbots
memory = TemporaryMemory()

# For conversation context
memory = InMemoryMemory(max_messages=50)

# For personalized assistants
memory = InMemoryMemory()
ltm = ReMeMemory(storage_path="./memory")

# For knowledge-intensive applications
ltm = Mem0Memory(api_key=os.environ["MEM0_API_KEY"])
```

### 2. Manage Memory Size

```python
# Prevent memory bloat
memory = InMemoryMemory(
    max_messages=100,
    max_tokens=8000,
    summarization=True,
    summarization_threshold=80  # Summarize at 80% capacity
)
```

### 3. Memory Cleanup

```python
# Periodic cleanup
if memory.size() > 100:
    # Option 1: Clear old messages
    memory.truncate(keep_last=50)
    
    # Option 2: Summarize and compress
    summary = await memory.summarize()
    memory.clear()
    memory.add(Msg(name="system", content=summary, role="system"))
```

### 4. Memory Sharing Between Agents

```python
# Share memory across agents
shared_memory = InMemoryMemory()

agent1 = DialogAgent(name="agent1", memory=shared_memory, ...)
agent2 = DialogAgent(name="agent2", memory=shared_memory, ...)

# Both agents see the same conversation history
```

### 5. Memory Serialization

```python
# Save memory state
state = memory.save_state()
with open("memory_state.json", "w") as f:
    json.dump(state, f)

# Load memory state
with open("memory_state.json", "r") as f:
    state = json.load(f)
memory.load_state(state)
```

## Memory Configuration Summary

```python
# Short-term only (simple chatbot)
config = {
    "memory": {"class_type": "InMemoryMemory"}
}

# Short-term + Long-term (personalized assistant)
config = {
    "memory": {"class_type": "InMemoryMemory"},
    "long_term_memory": {
        "class_type": "ReMeMemory",
        "storage_path": "./memory",
        "embedding_model": "text-embedding-v2"
    }
}

# Large context with summarization
config = {
    "memory": {
        "class_type": "InMemoryMemory",
        "max_messages": 200,
        "summarization": True
    }
}
```
