import asyncio

import matplotlib.pyplot as plt

from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.tool.tool_resource import Query
from app.toolkit.toolkit import Toolkit, ToolkitGraphType


async def main():
    """Main function."""
    # initialize toolkit
    toolkit = Toolkit()

    # create some sample actions
    action1 = Action(
        id="action1", name="Search Web", description="Search information from web"
    )
    action2 = Action(
        id="action2", name="Process File", description="Process file content"
    )
    action3 = Action(
        id="action3",
        name="Generate Code",
        description="Generate code based on description",
    )
    action4 = Action(
        id="action4",
        name="Analyze Data",
        description="Analyze data and create visualization",
    )

    # create some sample tools
    tool1: Tool = Query(id="tool1")
    tool2: Tool = Query(id="tool2")
    tool3: Tool = Query(id="tool3")
    tool4: Tool = Query(id="tool4")

    # add actions with connections
    toolkit.add_action(
        action=action1, next_actions=[(action2, 0.8), (action3, 0.6)], prev_actions=[]
    )

    toolkit.add_action(
        action=action2,
        next_actions=[(action3, 0.7), (action4, 0.9)],
        prev_actions=[(action1, 0.8)],
    )

    toolkit.add_action(
        action=action3,
        next_actions=[(action4, 0.7)],
        prev_actions=[(action1, 0.6), (action2, 0.7)],
    )

    toolkit.add_action(
        action=action4, next_actions=[], prev_actions=[(action2, 0.9), (action3, 0.7)]
    )

    # add tools with connections to actions
    toolkit.add_tool(tool=tool1, connected_actions=[(action1, 0.9)])
    toolkit.add_tool(tool=tool2, connected_actions=[(action2, 0.8)])
    toolkit.add_tool(tool=tool3, connected_actions=[(action3, 0.9)])
    toolkit.add_tool(tool=tool4, connected_actions=[(action4, 0.8)])

    # verify initial graph structure
    assert len(toolkit._toolkit_graph.nodes()) == 8, (
        "Graph should have 4 actions and 4 tools"
    )
    assert (
        len([
            n
            for n, d in toolkit._toolkit_graph.nodes(data=True)
            if d["type"] == ToolkitGraphType.ACTION
        ])
        == 4
    ), "Should have 4 action nodes"
    assert (
        len([
            n
            for n, d in toolkit._toolkit_graph.nodes(data=True)
            if d["type"] == ToolkitGraphType.TOOL
        ])
        == 4
    ), "Should have 4 tool nodes"

    # verify edge types and weights
    action_next_edges = [
        (u, v, d)
        for u, v, d in toolkit._toolkit_graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
    ]
    tool_call_edges = [
        (u, v, d)
        for u, v, d in toolkit._toolkit_graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_CALL_TOOL
    ]

    assert len(action_next_edges) == 5, "Should have 5 action-to-action edges"
    assert len(tool_call_edges) == 4, "Should have 4 action-to-tool edges"

    # verify all edge scores are within valid range
    assert all(
        0 <= d["score"] <= 1 for _, _, d in toolkit._toolkit_graph.edges(data=True)
    ), "All edge scores should be between 0 and 1"

    # visualize the full graph
    toolkit.visualize(toolkit._toolkit_graph, "Full Toolkit Graph")
    plt.show(block=False)

    print("\nTesting recommendation with different parameters:")

    # test different scenarios and verify results
    test_cases = [
        {
            "actions": [action1],
            "threshold": 0.5,
            "hops": 0,
            "title": "Subgraph: Start from Action1, No hops, Threshold 0.5",
            "expected_nodes": {action1.id, tool1.id},  # action1 and its tool
            "expected_edges": 1,  # just the tool call edge
        },
        {
            "actions": [action1],
            "threshold": 0.5,
            "hops": 1,
            "title": "Subgraph: Start from Action1, 1 hop, Threshold 0.5",
            "expected_nodes": {
                action1.id,
                action2.id,
                action3.id,
                tool1.id,
                tool2.id,
                tool3.id,
            },
            "expected_edges": 6,  # 3 next edges + 3 tool calls
        },
        {
            "actions": [action1],
            "threshold": 0.7,
            "hops": 2,
            "title": "Subgraph: Start from Action1, 2 hops, Threshold 0.7",
            "expected_nodes": {
                action1.id,
                action2.id,
                action3.id,
                action4.id,
                tool1.id,
                tool2.id,
                tool3.id,
                tool4.id,
            },
            "expected_edges": 8,  # 4 next edges  + 4 tool calls
        },
        {
            "actions": [action1, action3],
            "threshold": 0.6,
            "hops": 1,
            "title": "Subgraph: Start from Action1 & Action3, 1 hop, Threshold 0.6",
            "expected_nodes": {
                action1.id,
                action2.id,
                action3.id,
                action4.id,
                tool1.id,
                tool2.id,
                tool3.id,
                tool4.id,
            },
            "expected_edges": 9,  # 5 next edges  + 4 tool calls
        },
    ]

    for i, case in enumerate(test_cases):
        subgraph = await toolkit.recommend_tools(
            actions=case["actions"], threshold=case["threshold"], hops=case["hops"]
        )

        print(f"\nTest case {i + 1}:")
        print(f"Nodes: {subgraph.nodes()}")
        print(f"Edges: {subgraph.edges()}")

        # verify subgraph properties
        actual_nodes = set(subgraph.nodes())
        assert actual_nodes == case["expected_nodes"], (
            f"Test case {i + 1}: Expected nodes {case['expected_nodes']}, "
            f"got {actual_nodes}"
        )

        assert len(subgraph.edges()) == case["expected_edges"], (
            f"Test case {i + 1}: Expected {case['expected_edges']} edges, "
            f"got {len(subgraph.edges())}"
        )

        # verify edge properties in subgraph
        assert all(
            d["score"] >= case["threshold"] for _, _, d in subgraph.edges(data=True)
        ), f"Test case {i + 1}: All edges should have score >= {case['threshold']}"

        plt.figure(i + 2)
        toolkit.visualize(subgraph, case["title"])
        # plt.show(block=False)

    print("\nAll assertions passed! (press ctrl+c to exit)")
    plt.show()


if __name__ == "__main__":
    asyncio.run(main())
