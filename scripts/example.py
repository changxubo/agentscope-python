"""
AgentScope Basic Example

A minimal example demonstrating ReActAgent with tools.
This is the simplest way to get started with AgentScope.

Prerequisites:
    pip install agentscope

Usage:
    export DASHSCOPE_API_KEY=your_key
    python example.py
"""

import asyncio
import os
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, execute_python_code
from agentscope.message import Msg


async def main():
    """Run a simple agent interaction."""
    
    # Check API key
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Please set DASHSCOPE_API_KEY environment variable")
        return
    
    # Create toolkit with Python execution
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    
    # Create ReActAgent
    agent = ReActAgent(
        name="Assistant",
        sys_prompt="You are a helpful AI assistant. Use tools when needed.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        max_iters=10
    )
    
    # Interact with the agent
    print("=== AgentScope Example ===\n")
    
    msg = Msg(
        name="user",
        content="Calculate the first 10 Fibonacci numbers using Python",
        role="user"
    )
    
    response = await agent(msg)
    print(f"\nResponse: {response.get_text_content()}")


if __name__ == "__main__":
    asyncio.run(main())
