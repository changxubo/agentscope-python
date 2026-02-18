"""
AgentScope MsgHub Group Conversation Template

A production-ready template for multi-agent group discussions.
Messages from any participant are automatically broadcast to all others.

Use Cases:
- Multi-expert discussions
- Collaborative problem solving
- Debate and consensus building
- Team decision making

Usage:
    1. Set your API key: export DASHSCOPE_API_KEY=your_key
    2. Configure agents for your use case
    3. Run: python msghub_template.py
"""

import asyncio
import os
from agentscope.agent import DialogAgent
from agentscope.model import DashScopeChatModel
from agentscope.memory import InMemoryMemory
from agentscope.hub import MsgHub
from agentscope.message import Msg


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "qwen-max"

# Agent prompts for different expert roles
EXPERT_PROMPTS = {
    "Engineer": """You are a senior software engineer. In discussions:
- Focus on technical feasibility and implementation
- Consider scalability and performance
- Think about edge cases and potential issues
- Keep responses concise and actionable
""",

    "Designer": """You are a product designer. In discussions:
- Focus on user experience and usability
- Consider aesthetics and interaction patterns
- Think about accessibility and inclusivity
- Bring creative perspectives to problems
""",

    "Business": """You are a business strategist. In discussions:
- Focus on market fit and business value
- Consider costs and ROI
- Think about competitive advantages
- Bring customer and stakeholder perspectives
""",

    "Ethicist": """You are an ethics advisor. In discussions:
- Focus on ethical implications
- Consider fairness, privacy, and transparency
- Think about unintended consequences
- Raise concerns when needed
"""
}


# ============================================================
# AGENT FACTORY
# ============================================================

def create_expert_agent(name: str, sys_prompt: str) -> DialogAgent:
    """Create an expert agent for group discussion."""
    return DialogAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=DashScopeChatModel(
            model_name=MODEL_NAME,
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            stream=False  # Disable streaming for cleaner group output
        ),
        memory=InMemoryMemory()
    )


# ============================================================
# GROUP CONVERSATION PATTERNS
# ============================================================

async def round_robin_discussion():
    """
    Round-robin discussion where each agent speaks in turn.
    All messages auto-broadcast to other participants.
    """
    print("\n=== Round-Robin Group Discussion ===\n")
    
    # Create expert agents
    agents = {
        name: create_expert_agent(name, prompt)
        for name, prompt in EXPERT_PROMPTS.items()
    }
    
    # Discussion topic
    topic = "Should we build an AI-powered hiring assistant?"
    announcement = Msg(
        name="moderator",
        content=f"""Discussion Topic: {topic}
        
Each expert should share their perspective.
Consider: benefits, risks, implementation challenges, and ethical concerns.
Keep responses under 150 words. Listen and respond to other experts.""",
        role="user"
    )
    
    print(f"Topic: {topic}\n")
    print("Participants:", ", ".join(agents.keys()))
    print("\n" + "="*60 + "\n")
    
    # Run group discussion with MsgHub
    async with MsgHub(
        participants=list(agents.values()),
        announcement=announcement
    ) as hub:
        
        # Each agent speaks in turn
        for round_num in range(2):  # 2 rounds of discussion
            print(f"\n--- Round {round_num + 1} ---")
            
            for name, agent in agents.items():
                print(f"\n{name}:")
                response = await agent()
                print(f"  {response.get_text_content()}")


async def free_form_discussion():
    """
    Free-form discussion where agents respond to each other.
    Demonstrates dynamic membership and manual broadcast control.
    """
    print("\n=== Free-Form Group Discussion ===\n")
    
    # Create agents
    alice = create_expert_agent("Alice", 
        "You are Alice, a pragmatic thinker. Be concise and practical.")
    bob = create_expert_agent("Bob",
        "You are Bob, a creative thinker. Offer unconventional ideas.")
    charlie = create_expert_agent("Charlie",
        "You are Charlie, a critical thinker. Challenge assumptions.")
    
    agents = {"Alice": alice, "Bob": bob, "Charlie": charlie}
    
    topic = "What's the best approach to learn a new programming language?"
    
    print(f"Topic: {topic}\n")
    
    # Start with announcement
    async with MsgHub(
        participants=[alice, bob, charlie],
        announcement=Msg(name="user", content=topic, role="user")
    ) as hub:
        
        # Alice starts
        print("Alice:")
        response = await alice()
        print(f"  {response.get_text_content()}")
        
        # Bob responds to Alice
        print("\nBob (responding to Alice):")
        response = await bob()
        print(f"  {response.get_text_content()}")
        
        # Charlie joins the conversation
        print("\nCharlie (joining discussion):")
        response = await charlie()
        print(f"  {response.get_text_content()}")
        
        # Final round
        print("\n--- Final Thoughts ---")
        for name, agent in agents.items():
            response = await agent()
            print(f"{name}: {response.get_text_content()[:100]}...")


async def moderated_discussion():
    """
    Moderated discussion with structured turns and summarization.
    """
    print("\n=== Moderated Discussion with Summarizer ===\n")
    
    # Create participants
    expert1 = create_expert_agent("Expert1", 
        "Argue FOR the proposition. Be persuasive.")
    expert2 = create_expert_agent("Expert2",
        "Argue AGAINST the proposition. Be persuasive.")
    summarizer = create_expert_agent("Summarizer",
        "Summarize key points from both sides and find common ground.")
    
    proposition = "Remote work is better than office work for software teams."
    
    print(f"Proposition: {proposition}\n")
    
    async with MsgHub(
        participants=[expert1, expert2, summarizer],
        announcement=Msg(
            name="moderator",
            content=f"""Proposition: {proposition}

Expert1: Argue FOR the proposition.
Expert2: Argue AGAINST the proposition.
Summarizer: Wait for both arguments, then summarize and find common ground.""",
            role="user"
        )
    ) as hub:
        
        # Expert1 argues FOR
        print("Expert1 (FOR):")
        response = await expert1()
        print(f"  {response.get_text_content()}\n")
        
        # Expert2 argues AGAINST
        print("Expert2 (AGAINST):")
        response = await expert2()
        print(f"  {response.get_text_content()}\n")
        
        # Summarizer concludes
        print("Summarizer:")
        response = await summarizer()
        print(f"  {response.get_text_content()}")


async def dynamic_membership_discussion():
    """
    Discussion with dynamic agent joining/leaving.
    """
    print("\n=== Dynamic Membership Discussion ===\n")
    
    # Create initial participants
    alice = create_expert_agent("Alice", "You are Alice. Be thoughtful.")
    bob = create_expert_agent("Bob", "You are Bob. Be analytical.")
    
    # Agent that joins later
    charlie = create_expert_agent("Charlie", 
        "You are Charlie. You just joined. Catch up and contribute.")
    
    topic = "What makes a great engineering culture?"
    
    print(f"Topic: {topic}")
    print("Initial participants: Alice, Bob\n")
    
    async with MsgHub(
        participants=[alice, bob],
        announcement=Msg(name="user", content=topic, role="user")
    ) as hub:
        
        # Initial discussion
        print("Alice:")
        response = await alice()
        print(f"  {response.get_text_content()}")
        
        print("\nBob:")
        response = await bob()
        print(f"  {response.get_text_content()}")
        
        # Charlie joins dynamically
        print("\n--- Charlie joins the discussion ---")
        hub.register(charlie)
        
        # Send catch-up message
        hub.broadcast(Msg(
            name="system",
            content="Charlie has joined. Please continue the discussion.",
            role="system"
        ))
        
        print("\nCharlie:")
        response = await charlie()
        print(f"  {response.get_text_content()}")


# ============================================================
# MAIN
# ============================================================

async def main():
    """Run all MsgHub examples."""
    
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("Error: Please set DASHSCOPE_API_KEY environment variable")
        return
    
    # Example 1: Round-robin discussion
    await round_robin_discussion()
    
    # Example 2: Free-form discussion
    await free_form_discussion()
    
    # Example 3: Moderated discussion
    await moderated_discussion()
    
    # Example 4: Dynamic membership
    await dynamic_membership_discussion()


if __name__ == "__main__":
    asyncio.run(main())
