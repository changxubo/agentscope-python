# Distributed Deployment Reference

## Table of Contents
- [Actor-Based Architecture](#actor-based-architecture)
- [Local to Distributed Conversion](#local-to-distributed-conversion)
- [DistributedAgent](#distributedagent)
- [DistributedMsgHub](#distributedmsghub)
- [Deployment Patterns](#deployment-patterns)
- [Performance Optimization](#performance-optimization)

## Actor-Based Architecture

AgentScope uses an actor-based distributed execution framework built on Ray. This allows seamless scaling from local to distributed deployments.

### Key Concepts

- **Actor**: An independent unit of computation (agent) that processes messages
- **Message Passing**: Actors communicate exclusively through messages
- **Location Transparency**: Actors can run locally or remotely without code changes

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ray Runtime                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ Agent A  │───▶│ Agent B  │───▶│ Agent C  │   (Local/Remote)  │
│  │ (Actor)  │    │ (Actor)  │    │ (Actor)  │                   │
│  └──────────┘    └──────────┘    └──────────┘                   │
│       │               │               │                          │
│       └───────────────┴───────────────┘                          │
│                       │                                          │
│              ┌────────▼────────┐                                 │
│              │   MsgHub        │                                 │
│              │  (Coordinator)  │                                 │
│              └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Local to Distributed Conversion

### Step 1: Install Runtime

```bash
pip install agentscope-runtime
```

### Step 2: Local Development

```python
# local_app.py - Works locally
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel

agent = ReActAgent(
    name="assistant",
    model=OpenAIChatModel(model_name="gpt-4o", ...),
    ...
)

result = await agent(msg)
```

### Step 3: Convert to Distributed

```python
# distributed_app.py - Scales across cluster
from agentscope.agent import ReActAgent, to_dist_agent
from agentscope.model import OpenAIChatModel
import ray

# Initialize Ray
ray.init(address="auto")  # Connect to cluster

# Create agent and convert to distributed
local_agent = ReActAgent(
    name="assistant",
    model=OpenAIChatModel(model_name="gpt-4o", ...),
    ...
)
agent = to_dist_agent(local_agent)

# Usage is identical!
result = await agent(msg)
```

## DistributedAgent

### Creating Distributed Agents

```python
from agentscope.agent import DistributedAgent, ReActAgent
from agentscope.runtime import init_runtime

# Initialize distributed runtime
init_runtime(
    address="auto",  # Ray cluster address
    namespace="my_app"
)

# Create distributed agent directly
agent = DistributedAgent(
    name="worker_1",
    agent_class=ReActAgent,
    agent_config={
        "sys_prompt": "You are a worker agent.",
        "model": model_config,
        "toolkit": toolkit_config
    }
)

# Or wrap existing agent
from agentscope.agent import wrap_as_dist
agent = wrap_as_dist(local_agent)
```

### Distributed Agent Methods

```python
# All methods are remote calls
result = await agent(msg)              # Process message
history = await agent.get_memory()     # Get memory (remote)
await agent.clear_memory()             # Clear memory (remote)
```

## DistributedMsgHub

For multi-agent coordination in distributed settings:

```python
from agentscope.hub import DistributedMsgHub

# Create distributed hub
hub = DistributedMsgHub(
    name="team_hub",
    namespace="my_app"
)

# Register distributed agents
hub.register(agent1)
hub.register(agent2)
hub.register(agent3)

# Broadcast to all
hub.broadcast(msg)

# Route to specific agent
hub.route_to(msg, target="agent2")

# Get aggregated results
results = await hub.gather_all()
```

### DistributedMsgHub Configuration

```python
hub = DistributedMsgHub(
    name="coordinator",
    max_workers=10,           # Parallel worker limit
    timeout=30.0,             # Operation timeout
    retry_policy={
        "max_retries": 3,
        "backoff": "exponential"
    }
)
```

## Deployment Patterns

### Pattern 1: Master-Worker

```python
# One coordinator, multiple workers
from agentscope.agent import DialogAgent
from agentscope.hub import DistributedMsgHub

# Create workers
workers = [
    DistributedAgent(
        name=f"worker_{i}",
        agent_class=DialogAgent,
        agent_config={...}
    )
    for i in range(10)
]

# Create hub for coordination
hub = DistributedMsgHub(name="worker_pool")
for worker in workers:
    hub.register(worker)

# Distribute tasks
async def process_batch(tasks):
    results = []
    for i, task in enumerate(tasks):
        worker = workers[i % len(workers)]
        result = await worker(task)
        results.append(result)
    return results
```

### Pattern 2: Pipeline

```python
# Sequential processing through multiple agents
from agentscope.pipeline import DistributedPipeline

pipeline = DistributedPipeline([
    DistributedAgent(name="researcher", agent_class=ReActAgent, ...),
    DistributedAgent(name="analyst", agent_class=DialogAgent, ...),
    DistributedAgent(name="writer", agent_class=DialogAgent, ...),
])

# Process through pipeline
result = await pipeline(initial_msg)
# researcher -> analyst -> writer -> output
```

### Pattern 3: Fan-Out Fan-In

```python
from agentscope.pipeline import FanoutPipeline

# Parallel processing with aggregation
fanout = FanoutPipeline([
    DistributedAgent(name="sentiment", ...),     # Sentiment analysis
    DistributedAgent(name="entities", ...),      # Entity extraction
    DistributedAgent(name="summary", ...),       # Summarization
])

# Execute in parallel
results = await fanout(msg)
# Returns: {"sentiment": ..., "entities": ..., "summary": ...}

# Aggregate results
aggregator = DistributedAgent(name="aggregator", ...)
final = await aggregator(Msg(name="system", content=str(results), role="system"))
```

### Pattern 4: Hierarchical

```python
# Manager delegates to workers
class ManagerAgent(AgentBase):
    def __init__(self, workers, **kwargs):
        super().__init__(name="manager", **kwargs)
        self.workers = workers
        
    async def __call__(self, msg: Msg) -> Msg:
        # Analyze and delegate
        tasks = self.decompose(msg.content)
        
        # Distribute to workers
        results = await asyncio.gather(*[
            worker(Msg(name="manager", content=task, role="user"))
            for worker, task in zip(self.workers, tasks)
        ])
        
        # Aggregate and respond
        return self.aggregate(results)

# Deploy
manager = DistributedAgent(
    name="manager",
    agent_class=ManagerAgent,
    agent_config={"workers": [worker1, worker2, worker3]}
)
```

## Performance Optimization

### Parallel Execution

```python
from agentscope.runtime import parallel_execute

# Execute multiple agents in parallel
results = await parallel_execute(
    agents=[agent1, agent2, agent3],
    message=msg
)
```

### Automatic Optimization

AgentScope automatically optimizes parallel execution:

```python
from agentscope.runtime import enable_auto_parallel

# Enable automatic parallel execution detection
enable_auto_parallel()

# AgentScope will parallelize independent operations
result = await agent(msg)  # May execute tools in parallel
```

### Resource Management

```python
# Configure resource requirements per agent
agent = DistributedAgent(
    name="gpu_worker",
    agent_class=ReActAgent,
    agent_config={...},
    num_cpus=2,      # CPU cores
    num_gpus=0.5,    # GPU fraction
    memory=4096      # MB RAM
)
```

### Batching for Efficiency

```python
from agentscope.runtime import BatchProcessor

processor = BatchProcessor(
    agent=agent,
    batch_size=10,
    max_concurrent=5
)

# Process multiple inputs efficiently
results = await processor.process_batch(inputs)
```

## Cluster Configuration

### Starting a Ray Cluster

```bash
# Head node
ray start --head --port=6379

# Worker nodes
ray start --address='head-node:6379'
```

### Connecting to Cluster

```python
import ray

# From application
ray.init(address="head-node:6379")

# Or use auto-detection
ray.init(address="auto")
```

### Monitoring

```bash
# Ray dashboard
ray dashboard

# Check cluster status
ray status
```

## Error Handling

```python
from agentscope.runtime import DistributedError

try:
    result = await agent(msg)
except DistributedError as e:
    print(f"Agent {e.agent_name} failed: {e.message}")
    # Automatic retry based on retry policy
```

## Best Practices

1. **Design for idempotency** - Operations should be retry-safe
2. **Use appropriate batch sizes** - Balance latency and throughput
3. **Set timeouts** - Prevent hanging on failed nodes
4. **Monitor resource usage** - Avoid overloading workers
5. **Test locally first** - Use same code path for local/distributed
