"""
AgentScope ReActAgent Template

A production-ready template for creating a ReActAgent with tools.
Copy and modify this template for your specific use case.

Usage:
    1. Set your API key in environment: export DASHSCOPE_API_KEY=your_key
    2. Modify sys_prompt for your use case
    3. Add custom tools to the toolkit
    4. Run: python react_agent_template.py

SECURITY WARNING:
This template provides a secure starting point for building ReAct agents.
By default, it EXCLUDES dangerous tools like `execute_python_code` and
`execute_shell_command` that allow arbitrary code execution.

DO NOT enable these tools in production environments. Instead, build
specific, safe custom tools with input validation as shown in this template.
"""

import asyncio
import os
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
# SECURITY: execute_python_code and execute_shell_command are excluded by default
# as they allow arbitrary code execution. Add custom tools instead.
from agentscope.message import Msg


# ============================================================
# CONFIGURATION - Modify these for your use case
# ============================================================

AGENT_NAME = "Assistant"
AGENT_SYS_PROMPT = """You are a helpful AI assistant with coding capabilities.
When given a task:
1. Think through the problem step by step
2. Use available tools when needed
3. Provide clear, actionable responses
"""

MODEL_NAME = "qwen-max"
MAX_ITERS = 10


# ============================================================
# CUSTOM TOOLS - Add your custom tools here
# ============================================================

def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence (0-indexed)
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def get_current_time() -> str:
    """Get the current date and time.
    
    Returns:
        Current date and time as a formatted string
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# AGENT FACTORY
# ============================================================

def create_agent() -> ReActAgent:
    """Create and configure the ReActAgent."""
    
    # Create toolkit with safe custom tools only
    # SECURITY: Do NOT register execute_python_code or execute_shell_command
    # as they allow arbitrary code execution in production environments
    toolkit = Toolkit()
    
    # Add safe custom tools
    toolkit.register_tool_function(calculate_fibonacci)
    toolkit.register_tool_function(get_current_time)
    
    # Create the agent
    agent = ReActAgent(
        name=AGENT_NAME,
        sys_prompt=AGENT_SYS_PROMPT,
        model=DashScopeChatModel(
            model_name=MODEL_NAME,
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        max_iters=MAX_ITERS
    )
    
    return agent


# ============================================================
# MAIN INTERACTION LOOP
# ============================================================

async def main():
    """Main interaction loop."""
    
    # Check for API key
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Error: Please set DASHSCOPE_API_KEY environment variable")
        return
    
    # Create agent
    agent = create_agent()
    print(f"=== {AGENT_NAME} Ready ===")
    print("Type 'exit' to quit\n")
    
    # Conversation loop
    msg = None
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Create message and send to agent
            msg = Msg(name="user", content=user_input, role="user")
            msg = await agent(msg)
            
            # Print response
            print(f"\n{AGENT_NAME}: {msg.get_text_content()}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())
