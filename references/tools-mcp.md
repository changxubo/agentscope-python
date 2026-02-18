# Tools and MCP Integration Reference

## Table of Contents
- [Toolkit Overview](#toolkit-overview)
- [Built-in Tools](#built-in-tools)
- [Custom Tools](#custom-tools)
- [MCP Integration](#mcp-integration)
- [MCP Transport Types](#mcp-transport-types)

## Toolkit Overview

The `Toolkit` class manages tools that agents can use during execution.

```python
from agentscope.tool import Toolkit

# Create toolkit
toolkit = Toolkit()

# Register tools
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(execute_shell_command)

# Get all registered tools
tools = toolkit.get_tools()

# Execute a tool by name
result = await toolkit.execute_tool("execute_python_code", {"code": "print('hello')"})
```

## Built-in Tools

AgentScope provides several built-in tool functions:

### Code Execution

```python
from agentscope.tool import execute_python_code, execute_shell_command

# Python code execution
toolkit.register_tool_function(execute_python_code)

# Shell command execution
toolkit.register_tool_function(execute_shell_command)
```

### Web Tools

```python
from agentscope.tool import (
    web_search,          # Search the web
    web_fetch,           # Fetch web content
    web_browse,          # Browse and extract
)

toolkit.register_tool_function(web_search)
toolkit.register_tool_function(web_fetch)
```

### Document Processing

```python
from agentscope.tool import (
    docx_extract_text,   # Extract text from DOCX
    pdf_extract_text,    # Extract text from PDF
    excel_read_sheet,    # Read Excel sheets
)
```

## Custom Tools

### Method 1: Decorator

```python
from agentscope.tool import tool_function

@tool_function
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

# Register
toolkit.register_tool_function(calculate_fibonacci)
```

### Method 2: Tool Class

```python
from agentscope.tool import Tool

class WeatherTool(Tool):
    name = "get_weather"
    description = "Get current weather for a city"
    
    # JSON Schema for parameters
    parameters = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "default": "celsius"
            }
        },
        "required": ["city"]
    }
    
    async def execute(self, city: str, unit: str = "celsius") -> str:
        # Implementation
        return f"Weather in {city}: 22°{unit[0].upper()}"

# Register
toolkit.register_tool(WeatherTool())
```

### Method 3: Function with Schema

```python
def search_database(query: str, limit: int = 10) -> str:
    """Search the database for matching records."""
    # Implementation
    return f"Found {limit} results for '{query}'"

# Register with explicit schema
toolkit.register_tool_function(
    search_database,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "default": 10, "description": "Max results"}
        },
        "required": ["query"]
    }
)
```

## MCP Integration

AgentScope supports Model Context Protocol (MCP) for standardized tool integration.

### MCP Server Tools

Connect to MCP servers for tool access:

```python
from agentscope.tool import MCPToolkit

# Connect to MCP server
mcp_toolkit = MCPToolkit(
    server_name="my-mcp-server",
    transport="stdio",  # or "http", "streamable-http"
    command="python",
    args=["mcp_server.py"]
)

# Initialize connection
await mcp_toolkit.initialize()

# List available tools
tools = await mcp_toolkit.list_tools()

# Use with agent
agent = ReActAgent(
    name="mcp_agent",
    toolkit=mcp_toolkit,
    ...
)
```

### MCP Client Types

#### Stateless Client (New session per call)

```python
from agentscope.tool import StatelessMCPClient

client = StatelessMCPClient(
    server_url="http://localhost:8080/mcp"
)

# Each call creates a new session
result = await client.call_tool("search", {"query": "python"})
```

#### Stateful Client (Maintains session)

```python
from agentscope.tool import StatefulMCPClient

client = StatefulMCPClient(
    server_url="http://localhost:8080/mcp"
)

# Session is maintained across calls
await client.initialize()
result1 = await client.call_tool("create_session", {"user": "alice"})
result2 = await client.call_tool("query_session", {"query": "data"})
await client.close()
```

### Function-Level MCP Tools

Register individual MCP tools without full toolkit:

```python
from agentscope.tool import register_mcp_tool

# Register a specific MCP tool
await register_mcp_tool(
    toolkit=toolkit,
    server_name="filesystem-mcp",
    tool_name="read_file",
    transport="stdio",
    command="mcp-filesystem"
)
```

## MCP Transport Types

### 1. StdIO Transport

```python
# For local MCP servers
mcp_toolkit = MCPToolkit(
    server_name="local-server",
    transport="stdio",
    command="python",
    args=["server.py"],
    env={"API_KEY": "xxx"}  # Optional environment variables
)
```

### 2. HTTP Transport

```python
# For HTTP-based MCP servers
mcp_toolkit = MCPToolkit(
    server_name="http-server",
    transport="http",
    url="http://localhost:8080/mcp",
    headers={"Authorization": "Bearer token"}  # Optional headers
)
```

### 3. StreamableHTTP Transport

```python
# For streaming HTTP MCP servers
mcp_toolkit = MCPToolkit(
    server_name="streaming-server",
    transport="streamable-http",
    url="http://localhost:8080/mcp/stream"
)
```

## Higress AI Gateway Integration

For unified MCP tool access through API gateway:

```python
from agentscope.tool import HigressMCPToolkit

toolkit = HigressMCPToolkit(
    gateway_url="http://higress-gateway:8080",
    api_key="your-api-key"
)

# Access all MCP tools through gateway
tools = await toolkit.list_tools()
```

## Tool Execution Flow

```python
# 1. Agent receives message
msg = Msg(name="user", content="Calculate 2+2", role="user")

# 2. Agent decides to use tool (if ReActAgent)
# Internally:
#   - Model generates tool call
#   - Toolkit executes tool
#   - Result fed back to model
#   - Model generates final response

# 3. Manual tool execution
result = await toolkit.execute_tool(
    "execute_python_code",
    {"code": "print(2+2)"}
)
# Result: "4\n"
```

## Best Practices

1. **Use type hints** in tool functions for automatic schema generation
2. **Write clear docstrings** - they become tool descriptions
3. **Handle errors gracefully** - return error messages as strings
4. **Use async tools** for I/O-bound operations
5. **Validate parameters** before execution
6. **Prefer MCP tools** for external integrations
