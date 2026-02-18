"""
AgentScope Memory Management Template

A production-ready template for implementing memory systems
including short-term and long-term memory patterns.

Memory Types:
- InMemoryMemory: Short-term conversation history
- ReMeMemory: Long-term memory with semantic search
- Mem0Integration: External memory service

Usage:
    1. Set your API key: export DASHSCOPE_API_KEY=your_key
    2. Run: python memory_template.py
"""

import asyncio
import os
from agentscope.agent import ReActAgent, DialogAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg


# ============================================================
# PATTERN 1: BASIC SHORT-TERM MEMORY
# ============================================================

async def basic_short_term_memory():
    """
    Basic short-term memory for conversation history.
    
    Memory persists only during the session and is cleared
    when the agent is destroyed.
    """
    print("\n=== Basic Short-Term Memory ===\n")
    
    agent = DialogAgent(
        name="ChatBot",
        sys_prompt="You are a helpful assistant. Remember our conversation.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory()
    )
    
    # First message
    response1 = await agent(Msg(
        name="user",
        content="My name is Alice",
        role="user"
    ))
    print(f"User: My name is Alice")
    print(f"Bot: {response1.get_text_content()}\n")
    
    # Second message - agent remembers context
    response2 = await agent(Msg(
        name="user",
        content="What's my name?",
        role="user"
    ))
    print(f"User: What's my name?")
    print(f"Bot: {response2.get_text_content()}")


# ============================================================
# PATTERN 2: MEMORY WITH LIMITS
# ============================================================

async def memory_with_limits():
    """
    Memory with size limits and automatic summarization.
    
    Prevents memory from growing unbounded.
    """
    print("\n=== Memory with Limits ===\n")
    
    memory = InMemoryMemory(
        max_messages=10,        # Keep last 10 messages
        max_tokens=4000,        # Or limit by tokens
        summarization=True,     # Auto-summarize when limit reached
        summarization_threshold=0.8  # Summarize at 80% capacity
    )
    
    agent = DialogAgent(
        name="LimitedBot",
        sys_prompt="You are a helpful assistant.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=memory
    )
    
    # Have a conversation that would exceed limits
    for i in range(12):
        await agent(Msg(
            name="user",
            content=f"Message number {i+1}",
            role="user"
        ))
    
    # Memory automatically summarized oldest messages
    print(f"Memory size: {len(memory.get_memory())} messages")
    print("Oldest messages automatically summarized")


# ============================================================
# PATTERN 3: SHARED MEMORY BETWEEN AGENTS
# ============================================================

async def shared_memory():
    """
    Share memory between multiple agents.
    
    All agents see the same conversation history.
    """
    print("\n=== Shared Memory Between Agents ===\n")
    
    # Create shared memory
    shared_memory = InMemoryMemory()
    
    # Create two agents with shared memory
    agent1 = DialogAgent(
        name="Agent1",
        sys_prompt="You are Agent1. Work with Agent2.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=shared_memory
    )
    
    agent2 = DialogAgent(
        name="Agent2",
        sys_prompt="You are Agent2. Work with Agent1.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=shared_memory
    )
    
    # Agent1 receives message
    response1 = await agent1(Msg(
        name="user",
        content="Let's plan a project together",
        role="user"
    ))
    print(f"Agent1: {response1.get_text_content()}\n")
    
    # Agent2 sees Agent1's response (shared memory)
    response2 = await agent2(Msg(
        name="user",
        content="What did Agent1 suggest?",
        role="user"
    ))
    print(f"Agent2: {response2.get_text_content()}")


# ============================================================
# PATTERN 4: MEMORY PERSISTENCE
# ============================================================

async def memory_persistence():
    """
    Save and restore memory state for cross-session persistence.
    """
    print("\n=== Memory Persistence ===\n")
    
    import json
    
    memory_file = "memory_state.json"
    
    # Create agent
    agent = DialogAgent(
        name="PersistentBot",
        sys_prompt="You are a helpful assistant with long-term memory.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory()
    )
    
    # Have a conversation
    await agent(Msg(
        name="user",
        content="I'm working on a Python project",
        role="user"
    ))
    
    # Save memory state
    state = agent.memory.save_state()
    with open(memory_file, "w") as f:
        json.dump(state, f)
    print(f"Memory saved to {memory_file}")
    
    # Later: restore memory in new agent
    new_agent = DialogAgent(
        name="PersistentBot",
        sys_prompt="You are a helpful assistant with long-term memory.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory()
    )
    
    with open(memory_file, "r") as f:
        state = json.load(f)
    new_agent.memory.load_state(state)
    print("Memory restored in new agent")
    
    # New agent remembers previous conversation
    response = await new_agent(Msg(
        name="user",
        content="What project am I working on?",
        role="user"
    ))
    print(f"Bot: {response.get_text_content()}")


# ============================================================
# PATTERN 5: LONG-TERM MEMORY WITH REME
# ============================================================

async def long_term_memory_reme():
    """
    Long-term memory using ReMe for cross-session knowledge persistence.
    
    ReMe provides:
    - Semantic memory search
    - Experience summarization
    - Cross-session persistence
    """
    print("\n=== Long-Term Memory with ReMe ===\n")
    
    # Note: Requires reme-ai package installation
    # pip install reme-ai
    
    try:
        from agentscope.memory import ReMeMemory
        
        # Initialize ReMe memory
        ltm = ReMeMemory(
            storage_path="./reme_store",
            embedding_model="text-embedding-v2",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        )
        
        # Store a memory
        await ltm.add_memory(
            content="User prefers Python over JavaScript for backend development",
            metadata={
                "user_id": "user_123",
                "type": "preference",
                "timestamp": "2024-01-15"
            }
        )
        print("Memory stored: User preference for Python")
        
        # Search memories
        results = await ltm.search(
            query="What programming language does the user prefer?",
            top_k=5
        )
        
        print("\nRelevant memories found:")
        for result in results:
            print(f"  - {result['content']} (score: {result['score']:.2f})")
        
        # Extract from conversation trajectory
        trajectory = [
            Msg(name="user", content="Help me debug this Python code", role="user"),
            Msg(name="assistant", content="I found the issue in line 42...", role="assistant")
        ]
        
        await ltm.extract_from_conversation(
            messages=trajectory,
            user_id="user_123"
        )
        print("\nExtracted insights from conversation")
        
    except ImportError:
        print("ReMe not installed. Install with: pip install reme-ai")


# ============================================================
# PATTERN 6: MEMORY WITH MEM0
# ============================================================

async def long_term_memory_mem0():
    """
    Long-term memory using Mem0 external service.
    
    Mem0 provides managed memory with:
    - Automatic memory extraction
    - Semantic search
    - Multi-platform SDK
    """
    print("\n=== Long-Term Memory with Mem0 ===\n")
    
    try:
        from agentscope.memory import Mem0Memory
        
        # Initialize Mem0 memory
        memory = Mem0Memory(
            api_key=os.environ.get("MEM0_API_KEY"),
            user_id="user_123"
        )
        
        # Add memory from conversation
        await memory.add(
            messages=[
                {"role": "user", "content": "I work at TechCorp as a software engineer"},
                {"role": "assistant", "content": "I'll remember that you work at TechCorp as a software engineer."}
            ]
        )
        print("Memory added to Mem0")
        
        # Search memories
        results = await memory.search(
            query="Where does the user work?",
            top_k=5
        )
        
        print("\nSearch results:")
        for result in results:
            print(f"  - {result['memory']}")
        
        # Get all memories
        all_memories = await memory.get_all()
        print(f"\nTotal memories: {len(all_memories)}")
        
    except ImportError:
        print("Mem0 not configured. Set MEM0_API_KEY environment variable.")


# ============================================================
# PATTERN 7: COMBINED SHORT + LONG TERM MEMORY
# ============================================================

async def combined_memory():
    """
    Combine short-term conversation history with long-term knowledge.
    
    This is the recommended pattern for production agents.
    """
    print("\n=== Combined Short + Long Term Memory ===\n")
    
    from agentscope.memory import LongTermMemoryMode
    
    # Create agent with both memory types
    agent = ReActAgent(
        name="SmartAgent",
        sys_prompt="You are a helpful assistant with long-term memory of user preferences.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory(max_messages=50),  # Short-term
        # Uncomment when ReMe is configured:
        # long_term_memory_mode=LongTermMemoryMode.ENABLED,
        # long_term_memory=ReMeMemory(...)
    )
    
    # Agent has both:
    # - Short-term: Recent conversation context
    # - Long-term: Persistent knowledge about user
    
    print("Agent configured with combined memory system")


# ============================================================
# MAIN
# ============================================================

async def main():
    """Run all memory examples."""
    
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Error: Please set DASHSCOPE_API_KEY environment variable")
        return
    
    # Short-term memory patterns
    await basic_short_term_memory()
    await memory_with_limits()
    await shared_memory()
    await memory_persistence()
    
    # Long-term memory patterns
    await long_term_memory_reme()
    await long_term_memory_mem0()
    await combined_memory()


if __name__ == "__main__":
    asyncio.run(main())
