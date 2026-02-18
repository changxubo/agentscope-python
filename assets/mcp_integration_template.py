"""
AgentScope MCP Integration Template

A production-ready template for integrating Model Context Protocol (MCP)
servers with AgentScope agents.

MCP Transport Types:
- StdIO: Local MCP server via standard input/output
- HTTP: HTTP-based MCP server
- SSE: Server-Sent Events transport

Usage:
    1. Have an MCP server ready (or use a public one)
    2. Set your API key: export DASHSCOPE_API_KEY=your_key
    3. Configure MCP server connection
    4. Run: python mcp_integration_template.py
"""

import asyncio
import os
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, MCPToolkit
from agentscope.message import Msg


# ============================================================
# MCP SERVER CONFIGURATIONS
# ============================================================

# Example MCP server configurations
MCP_CONFIGS = {
    # StdIO transport - for local MCP servers
    "filesystem_stdio": {
        "server_name": "filesystem",
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "mcp_server_filesystem"],
        "env": {}  # Optional environment variables
    },
    
    # HTTP transport - for HTTP-based MCP servers
    "weather_http": {
        "server_name": "weather",
        "transport": "http",
        "url": "http://localhost:8080/mcp",
        "headers": {}  # Optional headers
    },
    
    # SSE transport - for Server-Sent Events
    "streaming_sse": {
        "server_name": "streaming",
        "transport": "sse",
        "url": "http://localhost:8080/mcp/sse"
    }
}


# ============================================================
# PATTERN 1: BASIC MCP TOOLKIT
# ============================================================

async def basic_mcp_toolkit():
    """
    Basic MCP integration using MCPToolkit.
    
    This connects to a single MCP server and uses all its tools.
    """
    print("\n=== Basic MCP Toolkit Integration ===\n")
    
    # Create MCP toolkit (using StdIO transport)
    # Replace with your actual MCP server configuration
    mcp_toolkit = MCPToolkit(
        server_name="example_server",
        transport="stdio",
        command="python",
        args=["mcp_server.py"]
    )
    
    try:
        # Initialize connection
        await mcp_toolkit.initialize()
        print("MCP connection initialized")
        
        # List available tools
        tools = await mcp_toolkit.list_tools()
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Create agent with MCP tools
        agent = ReActAgent(
            name="MCPAgent",
            sys_prompt="You have access to MCP tools. Use them to help the user.",
            model=DashScopeChatModel(
                model_name="qwen-max",
                api_key=os.environ.get("DASHSCOPE_API_KEY"),
                stream=True
            ),
            memory=InMemoryMemory(),
            formatter=DashScopeChatFormatter(),
            toolkit=mcp_toolkit
        )
        
        # Use the agent
        response = await agent(Msg(
            name="user",
            content="Help me with a task using your MCP tools",
            role="user"
        ))
        
        print(f"\nResponse: {response.get_text_content()}")
        
    finally:
        # Cleanup
        await mcp_toolkit.close()


# ============================================================
# PATTERN 2: MCP + CUSTOM TOOLS COMBINED
# ============================================================

async def combined_toolkit():
    """
    Combine MCP tools with custom local tools in a single toolkit.
    
    This is useful when you need both external MCP tools and
    custom tool implementations.
    """
    print("\n=== Combined MCP + Custom Tools ===\n")
    
    # Create standard toolkit
    toolkit = Toolkit()
    
    # Add custom local tools
    def get_system_info() -> str:
        """Get basic system information."""
        import platform
        return f"OS: {platform.system()}, Python: {platform.python_version()}"
    
    toolkit.register_tool_function(get_system_info)
    print("Added custom tool: get_system_info")
    
    # Add MCP tools (uncomment and configure for your MCP server)
    # mcp_client = await McpClientBuilder.create("my_mcp") \
    #     .stdio("python", ["mcp_server.py"]) \
    #     .build()
    # 
    # await toolkit.register_mcp_client(
    #     mcp_client,
    #     group_name="mcp_tools"
    # )
    # print("Added MCP tools from server")
    
    # Create agent with combined toolkit
    agent = ReActAgent(
        name="HybridAgent",
        sys_prompt="You have both local tools and MCP tools available.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit
    )
    
    response = await agent(Msg(
        name="user",
        content="What tools do you have available?",
        role="user"
    ))
    
    print(f"\nResponse: {response.get_text_content()}")


# ============================================================
# PATTERN 3: MULTIPLE MCP SERVERS
# ============================================================

async def multiple_mcp_servers():
    """
    Connect to multiple MCP servers for different tool categories.
    
    This is useful when you need tools from different sources.
    """
    print("\n=== Multiple MCP Servers ===\n")
    
    toolkit = Toolkit()
    
    # Add tools from first MCP server
    # filesystem_mcp = await McpClientBuilder.create("filesystem") \
    #     .stdio("mcp-filesystem") \
    #     .build()
    # await toolkit.register_mcp_client(filesystem_mcp, group_name="filesystem")
    # print("Added filesystem MCP tools")
    
    # Add tools from second MCP server
    # web_mcp = await McpClientBuilder.create("web") \
    #     .http("http://mcp-web-server:8080") \
    #     .build()
    # await toolkit.register_mcp_client(web_mcp, group_name="web")
    # print("Added web MCP tools")
    
    # Create agent with access to all MCP tools
    agent = ReActAgent(
        name="MultiMCPAgent",
        sys_prompt="""You have tools from multiple MCP servers:
- Filesystem tools for file operations
- Web tools for internet access
Choose the appropriate tool category for each task.""",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit
    )
    
    # Agent can now use tools from all connected MCP servers
    print("Agent configured with multiple MCP servers")


# ============================================================
# PATTERN 4: STATEFUL MCP CLIENT
# ============================================================

async def stateful_mcp_client():
    """
    Use stateful MCP client for sessions that maintain state.
    
    This is useful for MCP servers that track session-specific data.
    """
    print("\n=== Stateful MCP Client ===\n")
    
    from agentscope.tool.mcp import StatefulMCPClient
    
    # Create stateful client
    client = StatefulMCPClient(
        server_url="http://localhost:8080/mcp"
    )
    
    try:
        # Initialize session
        await client.initialize()
        print("Session initialized")
        
        # Multiple calls maintain session state
        result1 = await client.call_tool(
            "create_workspace",
            {"name": "project_alpha"}
        )
        print(f"Created workspace: {result1}")
        
        result2 = await client.call_tool(
            "add_item",
            {"item": "Task 1"}
        )
        print(f"Added item: {result2}")
        
        # Session maintains context across calls
        
    finally:
        await client.close()


# ============================================================
# PATTERN 5: MCP THROUGH HIGRESS AI GATEWAY
# ============================================================

async def higress_gateway_integration():
    """
    Use Higress AI Gateway for unified MCP tool access.
    
    This provides a single API endpoint for multiple MCP servers
    with authentication, rate limiting, and monitoring.
    """
    print("\n=== Higress AI Gateway Integration ===\n")
    
    from agentscope.tool import HigressMCPToolkit
    
    # Connect through Higress gateway
    toolkit = HigressMCPToolkit(
        gateway_url="http://higress-gateway:8080",
        api_key=os.environ.get("HIGRESS_API_KEY")
    )
    
    # Initialize and list available tools
    await toolkit.initialize()
    
    tools = await toolkit.list_tools()
    print(f"Tools available through gateway: {len(tools)}")
    
    # Create agent with gateway-provided tools
    agent = ReActAgent(
        name="GatewayAgent",
        sys_prompt="You access MCP tools through a unified gateway.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit
    )


# ============================================================
# HELPER: CREATE MCP SERVER FOR TESTING
# ============================================================

def create_test_mcp_server():
    """
    Create a simple test MCP server for development.
    
    Run this to create a local MCP server for testing integrations.
    """
    server_code = '''
"""Simple test MCP server"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("test-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="echo",
            description="Echo back a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "echo":
        return [TextContent(
            type="text",
            text=f"Echo: {arguments['message']}"
        )]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
'''
    
    with open("test_mcp_server.py", "w") as f:
        f.write(server_code)
    
    print("Created test_mcp_server.py")
    print("Run with: python test_mcp_server.py")


# ============================================================
# MAIN
# ============================================================

async def main():
    """Run MCP integration examples."""
    
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Error: Please set DASHSCOPE_API_KEY environment variable")
        return
    
    print("MCP Integration Templates")
    print("=" * 50)
    print("\nNote: These examples require MCP servers to be running.")
    print("Uncomment the MCP connection code and configure for your servers.\n")
    
    # Example 1: Basic MCP toolkit
    # await basic_mcp_toolkit()
    
    # Example 2: Combined tools
    await combined_toolkit()
    
    # Example 3: Multiple MCP servers
    # await multiple_mcp_servers()
    
    # Example 4: Stateful client
    # await stateful_mcp_client()
    
    # Example 5: Higress gateway
    # await higress_gateway_integration()


if __name__ == "__main__":
    asyncio.run(main())
