import os

from app.agent.reasoner.dual_llm import DualLLMReasoner
from app.agent.workflow.operator.operator import Operator
from app.toolkit.action.action import Action
from app.toolkit.tool.tool_resource import Query
from app.toolkit.toolkit import Toolkit


async def main():
    """Main function to demonstrate Operator usage."""
    # Initialize toolkit
    toolkit = Toolkit()

    # Create actions
    action1 = Action(
        id="search",
        name="Search Knowledge",
        description="Search relevant information from knowledge base",
    )
    action2 = Action(
        id="analyze",
        name="Analyze Content",
        description="Analyze and extract insights from content",
    )
    action3 = Action(
        id="generate",
        name="Generate Response",
        description="Generate response based on analysis",
    )

    # Create tools
    search_tool = Query(tool_id="search_tool")
    analyze_tool = Query(tool_id="analyze_tool")
    generate_tool = Query(tool_id="generate_tool")

    # Add actions to toolkit
    toolkit.add_action(action=action1, next_actions=[(action2, 0.9)], prev_actions=[])
    toolkit.add_action(
        action=action2, next_actions=[(action3, 0.8)], prev_actions=[(action1, 0.9)]
    )
    toolkit.add_action(action=action3, next_actions=[], prev_actions=[(action2, 0.8)])

    # Add tools to toolkit
    toolkit.add_tool(tool=search_tool, connected_actions=[(action1, 0.9)])
    toolkit.add_tool(tool=analyze_tool, connected_actions=[(action2, 0.9)])
    toolkit.add_tool(tool=generate_tool, connected_actions=[(action3, 0.9)])

    # Create operator
    operator = Operator(
        op_id="test_operator",
        toolkit=toolkit,
        actions=[action1],
    )
    await operator.initialize(threshold=0.7, hops=2)

    # Set operator properties
    operator.task = """
    Answer user questions about movies by:
    1. Find currently popular movies and their ratings
    2. Extract movie-related user preferences from chat history
    3. Generate personalized movie recommendations
    The response should include specific movie titles, their ratings, and brief explanations for each recommendation.
    Answer in Chinese.
    """

    operator.context = """
    User's chat history:
    - "I loved The Dark Knight trilogy, especially the complex characters"
    - "Not a fan of romantic comedies, they're too predictable"
    - "Really enjoyed Inception and Interstellar, love mind-bending plots"
    - "Looking for new movies similar to these"
    
    Current user query: "Can you recommend some movies I might like? I want something with good ratings from recent years."
    
    Additional context:
    - User preference: Complex plots, psychological elements
    - Genre preference: Action, sci-fi, thriller
    - Recent viewing history: Mostly Christopher Nolan films
    """

    operator.scratchpad = """
    Current analysis:
    1. User Profile
       - Strong preference for complex narratives
       - Enjoys psychological and cerebral elements
       - Appreciates well-crafted action sequences
       - Values director's artistry (Nolan fan)
    
    2. Search Parameters
       - Focus: Recent critically acclaimed films
       - Genres: Action, Sci-fi, Thriller
       - Must have: Complex plot, psychological elements
       - Avoid: Romantic comedies, simplistic narratives
    """

    # Initialize reasoner (mock for demonstration)
    openai_api_base = os.getenv("OPENAI_API_BASE")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    reasoner = DualLLMReasoner(
        model_config={
            "model_alias": "gpt-4o-mini",
            "api_base": openai_api_base,
            "api_key": openai_api_key,
        }
    )

    # Test operator functionality
    print("Testing operator...")

    # Verify initial state
    assert operator.id == "test_operator", "Operator ID should match"
    assert len(operator.actions) == 1, "Should start with one action"
    assert operator.toolkit is not None, "Toolkit should be initialized"

    # Get recommended actions
    recommended_actions = await operator.get_recommanded_actions(threshold=0.7, hops=2)
    assert len(recommended_actions) == 3, "Should have recommended 3 actions"

    # Get tools
    tools = operator.get_tools_from_actions()
    assert len(tools) == 3, "Should have tools available"

    # Format prompt
    prompt = await operator.format_operation_prompt()
    assert all(
        section in prompt for section in ["Task", "Context", "Actions", "Tools"]
    ), "Prompt should contain all required sections"

    # Execute operator (with minimal reasoning rounds for testing)
    await operator.execute(
        reasoner=reasoner,
        reasoning_rounds=5,
        print_messages=True,
    )
    print("Operator execution completed successfully")

    # Verify final state
    assert operator.recommanded_actions is not None, (
        "Should have recommended actions after execution"
    )

    print("All tests passed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
