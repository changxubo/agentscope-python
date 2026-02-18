# Pipelines and Orchestration Reference

## Table of Contents
- [Pipeline Overview](#pipeline-overview)
- [Sequential Pipeline](#sequential-pipeline)
- [Fanout Pipeline (Parallel)](#fanout-pipeline-parallel)
- [Custom Pipelines](#custom-pipelines)
- [Planning Module](#planning-module)
- [Conditional Routing](#conditional-routing)

## Pipeline Overview

Pipelines orchestrate multiple agents into workflows. They define how messages flow between agents.

### Available Pipeline Types

| Pipeline | Execution | Use Case |
|----------|-----------|----------|
| `sequential_pipeline` | Serial, one after another | Step-by-step processing |
| `fanout_pipeline` | Parallel, all at once | Multiple analyses simultaneously |
| `ConditionalPipeline` | Route based on conditions | Dynamic workflows |
| `LoopPipeline` | Repeat until condition | Iterative refinement |

## Sequential Pipeline

Execute agents in order, passing output from one to the next.

```python
from agentscope.pipeline import sequential_pipeline
from agentscope.agent import DialogAgent

# Create agents
researcher = DialogAgent(name="researcher", sys_prompt="Research the topic...", ...)
analyst = DialogAgent(name="analyst", sys_prompt="Analyze findings...", ...)
writer = DialogAgent(name="writer", sys_prompt="Write a summary...", ...)

# Create sequential pipeline
pipeline = sequential_pipeline([researcher, analyst, writer])

# Execute
result = await pipeline(Msg(name="user", content="Explain quantum computing", role="user"))
# Flow: researcher -> analyst -> writer -> final output
```

### With Shared Memory

```python
from agentscope.memory import InMemoryMemory

# Share memory across pipeline
shared_memory = InMemoryMemory()

researcher = DialogAgent(name="researcher", memory=shared_memory, ...)
analyst = DialogAgent(name="analyst", memory=shared_memory, ...)
writer = DialogAgent(name="writer", memory=shared_memory, ...)

pipeline = sequential_pipeline([researcher, analyst, writer])
```

### Pipeline with Intermediate Access

```python
from agentscope.pipeline import SequentialPipeline

pipeline = SequentialPipeline(
    agents=[agent1, agent2, agent3],
    return_intermediate=True  # Return all intermediate results
)

result = await pipeline(msg)
# result = {
#     "agent1": <output1>,
#     "agent2": <output2>,
#     "agent3": <output3>  # final
# }
```

## Fanout Pipeline (Parallel)

Execute multiple agents in parallel on the same input.

```python
from agentscope.pipeline import fanout_pipeline

# Create specialized agents
sentiment_agent = DialogAgent(name="sentiment", ...)
entity_agent = DialogAgent(name="entities", ...)
summary_agent = DialogAgent(name="summary", ...)

# Execute all in parallel
pipeline = fanout_pipeline([sentiment_agent, entity_agent, summary_agent])

result = await pipeline(Msg(name="user", content="Apple announced new iPhone", role="user"))
# result = {
#     "sentiment": "positive",
#     "entities": ["Apple", "iPhone"],
#     "summary": "Apple product announcement..."
# }
```

### FanoutPipeline Object (Reusable)

```python
from agentscope.pipeline import FanoutPipeline

# Create reusable pipeline
pipeline = FanoutPipeline(
    agents=[agent1, agent2, agent3],
    max_concurrent=5,  # Limit concurrent executions
    timeout=30.0       # Timeout per agent
)

# Reuse for multiple inputs
results = []
for input_msg in inputs:
    result = await pipeline(input_msg)
    results.append(result)
```

### Fanout with Aggregation

```python
from agentscope.pipeline import FanoutPipeline

# Parallel analysis + aggregation
fanout = FanoutPipeline(
    agents=[analyzer1, analyzer2, analyzer3],
    aggregator=aggregator_agent  # Optional: aggregates all results
)

result = await pipeline(msg)
# Automatically aggregates parallel results through aggregator_agent
```

## Custom Pipelines

### Branching Pipeline

```python
from agentscope.pipeline import Pipeline

class BranchingPipeline(Pipeline):
    def __init__(self, agents, router):
        super().__init__()
        self.agents = agents
        self.router = router  # Function to select agent
        
    async def __call__(self, msg: Msg) -> Msg:
        # Route to appropriate agent
        agent_name = self.router(msg.content)
        agent = self.agents[agent_name]
        return await agent(msg)

# Usage
def route_by_topic(content):
    if "code" in content.lower():
        return "coder"
    elif "write" in content.lower():
        return "writer"
    else:
        return "general"

pipeline = BranchingPipeline(
    agents={
        "coder": coder_agent,
        "writer": writer_agent,
        "general": general_agent
    },
    router=route_by_topic
)
```

### Loop Pipeline

```python
from agentscope.pipeline import Pipeline

class LoopPipeline(Pipeline):
    def __init__(self, agent, max_iterations=5, stop_condition=None):
        super().__init__()
        self.agent = agent
        self.max_iterations = max_iterations
        self.stop_condition = stop_condition
        
    async def __call__(self, msg: Msg) -> Msg:
        current = msg
        for i in range(self.max_iterations):
            result = await self.agent(current)
            
            # Check stop condition
            if self.stop_condition and self.stop_condition(result):
                return result
                
            # Feed output back as input
            current = result
            
        return current

# Usage: Refine until satisfied
def is_complete(msg):
    return "COMPLETE" in msg.content

refinement = LoopPipeline(
    agent=refiner_agent,
    max_iterations=10,
    stop_condition=is_complete
)
```

## Planning Module

AgentScope includes a planning module for task decomposition and management.

### Plan Management Tools

```python
from agentscope.tool import (
    create_plan,           # Create execution plan
    view_subtasks,         # View current subtasks
    revise_current_plan,   # Revise the plan
    update_subtask_state,  # Update subtask status
    finish_subtask,        # Mark subtask complete
    finish_plan,           # Mark entire plan complete
    view_historical_plans, # View past plans
    recover_historical_plan # Restore previous plan
)

# Register with toolkit
toolkit = Toolkit()
toolkit.register_tool_function(create_plan)
toolkit.register_tool_function(view_subtasks)
toolkit.register_tool_function(finish_subtask)
# ... etc
```

### Agent with Planning

```python
from agentscope.agent import ReActAgent

# Agent can create and manage its own plans
agent = ReActAgent(
    name="planner",
    sys_prompt="""You are a planning agent. When given a complex task:
    1. Use create_plan to break it into subtasks
    2. Execute each subtask
    3. Use finish_subtask after completing each
    4. Use finish_plan when all subtasks are done
    """,
    toolkit=toolkit,
    ...
)

# Agent will autonomously plan and execute
result = await agent(Msg(
    name="user", 
    content="Build a web scraper that extracts product prices", 
    role="user"
))
```

### Plan Data Structure

```python
# Plan structure
plan = {
    "id": "plan_001",
    "description": "Build web scraper",
    "subtasks": [
        {
            "id": "subtask_1",
            "description": "Research target website",
            "status": "completed"
        },
        {
            "id": "subtask_2", 
            "description": "Implement scraper",
            "status": "in_progress"
        },
        {
            "id": "subtask_3",
            "description": "Add error handling",
            "status": "pending"
        }
    ],
    "created_at": "2024-01-15T10:00:00",
    "status": "in_progress"
}
```

### Hint Messages

Guide agent execution with hints:

```python
from agentscope.plan import PlanExecutor

executor = PlanExecutor(agent=agent)

# Add hint messages
executor.add_hint("Focus on Python libraries like BeautifulSoup")
executor.add_hint("Handle rate limiting gracefully")

# Execute with hints
result = await executor.execute(task)
```

## Conditional Routing

### Route by Content

```python
from agentscope.pipeline import ConditionalPipeline

pipeline = ConditionalPipeline(
    routes={
        "code": {"condition": lambda m: "code" in m.content.lower(), "agent": coder},
        "chat": {"condition": lambda m: True, "agent": chatter}  # default
    }
)

result = await pipeline(msg)
```

### Route by Agent Decision

```python
from agentscope.agent import DialogAgent

# Router agent decides which specialist to use
router = DialogAgent(
    name="router",
    sys_prompt="""Decide which agent should handle this query:
    - 'researcher': for factual questions
    - 'coder': for programming tasks
    - 'writer': for content creation
    Reply with just the agent name.""",
    ...
)

class RoutingPipeline(Pipeline):
    async def __call__(self, msg: Msg) -> Msg:
        # Ask router
        route = await self.router(msg)
        
        # Select agent
        agent = self.agents[route.content.strip()]
        
        # Execute
        return await agent(msg)
```

## Pipeline Composition

Combine pipelines for complex workflows:

```python
from agentscope.pipeline import sequential_pipeline, fanout_pipeline

# Research phase (sequential)
research = sequential_pipeline([searcher, summarizer])

# Analysis phase (parallel)
analysis = fanout_pipeline([sentiment_analyzer, entity_extractor, fact_checker])

# Final phase (sequential)
final = sequential_pipeline([aggregator, editor])

# Compose into master pipeline
master_pipeline = sequential_pipeline([research, analysis, final])

# Execute
result = await master_pipeline(initial_msg)
```

## Best Practices

1. **Match pipeline to task** - Sequential for dependencies, parallel for independence
2. **Set timeouts** - Prevent cascading failures
3. **Use shared memory** when agents need context from previous steps
4. **Plan complex tasks** - Use planning module for decomposition
5. **Handle errors gracefully** - Add fallback agents
