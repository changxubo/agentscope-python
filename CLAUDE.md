# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains an Agent Skill for building production-ready multi-agent applications using Alibaba's AgentScope framework. It enables the creation of various agent types, orchestration of multi-agent workflows, and integration with different models and tools.

## Core Architecture & Patterns

The framework is structured around several key patterns for building agent-based applications.

### 1. Agent Types

- **`DialogAgent`**: For simple conversational agents, chatbots, and Q&A systems.
- **`ReActAgent`**: A tool-using agent that follows the ReAct (Reason+Act) pattern. It can use a `Toolkit` of registered functions to perform tasks.
- **Custom Agents**: You can create specialized agents by inheriting from `AgentBase` and implementing the `__call__` method.

### 2. Multi-Agent Orchestration

- **Pipelines**:
  - `sequential_pipeline`: Chains agents together where the output of one is the input for the next (e.g., `researcher -> analyzer -> writer`).
  - `fanout_pipeline`: Sends the same input to multiple agents for parallel processing (e.g., for sentiment analysis, entity extraction, and summarization).
- **`MsgHub`**: Facilitates group discussions where multiple agents can communicate and react to each other's messages in a shared context.

### 3. Application Structure (`AgentApp`)

Production applications should follow a three-stage lifecycle by subclassing `AgentApp`:
1.  `init()`: Initialize resources, agents, and toolkits.
2.  `query()`: Process user input and return the agent's response.
3.  `shutdown()`: Clean up resources.

### 4. Tool Integration (Toolkits)

- **`Toolkit`**: A container for tools that can be passed to an agent (e.g., `ReActAgent`).
- **Custom Tools**: Tools are standard Python functions registered with a `Toolkit` instance.
- **MCP (Model Context Protocol)**: The `MCPToolkit` allows agents to connect to external MCP servers to access a broader ecosystem of tools.

**CRITICAL SECURITY NOTE**: The built-in tools `execute_shell_command` and `execute_python_code` are extremely dangerous and should **NEVER** be used in production. They allow arbitrary code execution. Always create safe, specific custom tools with proper input validation and sandboxing instead.

### 5. Model and Memory Configuration

- **Model Support**: The framework supports various model providers through wrappers like `DashScopeChatModel` (Qwen), `OpenAIChatModel` (GPT), and `AnthropicChatModel` (Claude).
- **Formatters**: It is crucial to match the correct formatter (e.g., `DashScopeChatFormatter`) to the model being used to ensure proper message formatting.
- **Memory**:
  - `InMemoryMemory`: For short-term conversation history.
  - `ReMeMemory`: For long-term, cross-session memory using embeddings.

### 6. Distributed Deployment

Local agents can be converted to distributed agents for deployment in a cluster using `ray`. The `to_dist_agent` function handles this conversion, allowing the same agent logic to be used in both local and distributed environments.

## Common Commands & Usage

This project is a "skill" and doesn't have traditional build or test commands. Development focuses on using the AgentScope library.

**Installation:**
To install this skill:
```bash
npx skills add https://github.com/changxubo/agentscope-python --skill agentscope
```

**Running Examples:**
The `scripts/` directory contains runnable examples. To run them:
```bash
python scripts/example.py
```
*Note: You may need to set environment variables like `DASHSCOPE_API_KEY` as shown in the example code.*

## File Structure

- `README.md`: Main project documentation with code snippets for core patterns.
- `SKILL.md`: Skill definition and documentation, including security warnings and best practices. It provides a good overview of how the skill should be used.
- `agentscope.skill`: The manifest file for the skill.
- `references/`: Detailed markdown documentation for specific components like agents, tools, memory, and pipelines. A very useful resource for in-depth understanding.
- `scripts/`: Contains runnable example scripts demonstrating various features of the AgentScope framework.
