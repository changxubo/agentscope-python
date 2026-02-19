"""
AgentScope Multi-Agent Pipeline Template

A production-ready template for multi-agent workflows using pipelines.
Demonstrates sequential and parallel execution patterns.

Usage:
    1. Set your API key: export DASHSCOPE_API_KEY=your_key
    2. Modify agent configurations for your use case
    3. Run: python multi_agent_pipeline_template.py
"""

import asyncio
import os
from agentscope.agent import ReActAgent, DialogAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
# SECURITY: execute_python_code excluded - allows arbitrary code execution
from agentscope.pipeline import sequential_pipeline, fanout_pipeline
from agentscope.message import Msg


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "qwen-max"

RESEARCHER_PROMPT = """You are a research specialist. Your job is to:
1. Gather comprehensive information on the given topic
2. Identify key facts, trends, and insights
3. Provide a structured summary of findings
"""

ANALYST_PROMPT = """You are a data analyst. Your job is to:
1. Analyze the research findings
2. Identify patterns and connections
3. Extract actionable insights
"""

WRITER_PROMPT = """You are a technical writer. Your job is to:
1. Synthesize research and analysis
2. Create clear, engaging content
3. Structure the output for readability
"""

SENTIMENT_PROMPT = """You are a sentiment analyzer. Determine the emotional tone of text.
Return: positive, negative, or neutral with confidence score.
"""

ENTITY_PROMPT = """You are an entity extractor. Identify and categorize:
- People, Organizations, Locations
- Dates, Numbers, Percentages
Return as structured JSON.
"""

SUMMARY_PROMPT = """You are a summarizer. Create concise summaries that:
1. Capture key points
2. Maintain accuracy
3. Stay under 200 words
"""


# ============================================================
# AGENT FACTORIES
# ============================================================

def create_tool_agent(name: str, sys_prompt: str) -> ReActAgent:
    """Create an agent with safe tool access."""
    toolkit = Toolkit()
    # SECURITY: Do NOT register execute_python_code in production
    # Add your safe custom tools here instead
    
    return ReActAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=DashScopeChatModel(
            model_name=MODEL_NAME,
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            stream=True
        ),
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        max_iters=5
    )


def create_simple_agent(name: str, sys_prompt: str) -> DialogAgent:
    """Create a simple conversational agent."""
    return DialogAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=DashScopeChatModel(
            model_name=MODEL_NAME,
            api_key=os.environ.get("DASHSCOPE_API_KEY")
        ),
        memory=InMemoryMemory()
    )


# ============================================================
# WORKFLOW EXAMPLES
# ============================================================

async def sequential_workflow_example():
    """
    Sequential Pipeline: Research → Analysis → Writing
    
    Use Case: Step-by-step content creation where each agent
    builds on the output of the previous agent.
    """
    print("\n=== Sequential Pipeline: Research → Analysis → Writing ===\n")
    
    # Create agents for sequential workflow
    researcher = create_tool_agent("Researcher", RESEARCHER_PROMPT)
    analyst = create_simple_agent("Analyst", ANALYST_PROMPT)
    writer = create_simple_agent("Writer", WRITER_PROMPT)
    
    # Execute sequential pipeline
    topic = "The future of AI agents in enterprise applications"
    result = await sequential_pipeline(
        agents=[researcher, analyst, writer],
        msg=Msg(name="user", content=topic, role="user")
    )
    
    print(f"Topic: {topic}")
    print(f"\nFinal Output:\n{result.get_text_content()}")
    return result


async def parallel_workflow_example():
    """
    Fanout Pipeline: Parallel Analysis
    
    Use Case: Multiple independent analyses on the same input,
    useful for comprehensive understanding.
    """
    print("\n=== Fanout Pipeline: Parallel Analysis ===\n")
    
    # Create agents for parallel analysis
    sentiment_agent = create_simple_agent("Sentiment", SENTIMENT_PROMPT)
    entity_agent = create_simple_agent("Entity", ENTITY_PROMPT)
    summary_agent = create_simple_agent("Summary", SUMMARY_PROMPT)
    
    # Execute parallel pipeline
    text = """
    Apple Inc. announced record-breaking Q4 earnings of $89.5 billion,
    representing 8% year-over-year growth. CEO Tim Cook expressed optimism
    about AI integration across the product lineup, while analysts remain
    cautiously positive about the company's innovation trajectory.
    """
    
    results = await fanout_pipeline(
        agents=[sentiment_agent, entity_agent, summary_agent],
        msg=Msg(name="user", content=text.strip(), role="user"),
        enable_gather=True
    )
    
    print(f"Input Text: {text.strip()}")
    print("\n--- Parallel Results ---")
    
    for agent_name, result in results.items():
        print(f"\n{agent_name}:")
        print(result.get_text_content())
    
    return results


async def hybrid_workflow_example():
    """
    Combined Workflow: Parallel Research → Sequential Synthesis
    
    Use Case: Gather multiple perspectives in parallel,
    then synthesize sequentially.
    """
    print("\n=== Hybrid Workflow: Parallel → Sequential ===\n")
    
    # Phase 1: Parallel research from different angles
    tech_researcher = create_simple_agent("TechResearcher", 
        "Research technology aspects of the topic")
    market_researcher = create_simple_agent("MarketResearcher",
        "Research market and business aspects")
    trend_researcher = create_simple_agent("TrendResearcher",
        "Research future trends and predictions")
    
    topic = "Generative AI in Healthcare"
    
    # Parallel research
    research_results = await fanout_pipeline(
        agents=[tech_researcher, market_researcher, trend_researcher],
        msg=Msg(name="user", content=topic, role="user"),
        enable_gather=True
    )
    
    print(f"Topic: {topic}")
    print("\n--- Research Phase (Parallel) ---")
    for name, result in research_results.items():
        print(f"\n{name}: {result.get_text_content()[:200]}...")
    
    # Phase 2: Sequential synthesis
    print("\n--- Synthesis Phase (Sequential) ---")
    
    aggregator = create_simple_agent("Aggregator",
        "Combine multiple research inputs into a cohesive summary")
    editor = create_simple_agent("Editor",
        "Polish and finalize the report")
    
    # Combine research into single message
    combined_content = "\n\n".join([
        f"## {name}\n{result.get_text_content()}"
        for name, result in research_results.items()
    ])
    
    final_result = await sequential_pipeline(
        agents=[aggregator, editor],
        msg=Msg(name="user", content=combined_content, role="user")
    )
    
    print(f"\nFinal Report:\n{final_result.get_text_content()}")
    return final_result


# ============================================================
# MAIN
# ============================================================

async def main():
    """Run all workflow examples."""
    
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Error: Please set DASHSCOPE_API_KEY environment variable")
        return
    
    # Example 1: Sequential workflow
    await sequential_workflow_example()
    
    # Example 2: Parallel workflow
    await parallel_workflow_example()
    
    # Example 3: Hybrid workflow
    await hybrid_workflow_example()


if __name__ == "__main__":
    asyncio.run(main())
