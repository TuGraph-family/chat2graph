import matplotlib.pyplot as plt

from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit
from test.resource.tool_resource import Query


def main():
    """Main function."""
    # initialize toolkit
    toolkit_service = ToolkitService()

    # create some sample actions
    action1 = Action(id="action1", name="Search Web", description="Search information from web")
    action2 = Action(id="action2", name="Process File", description="Process file content")
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
    toolkit_service.add_action(
        action=action1,
        next_actions=[(action2, 0.8), (action3, 0.6)],
        prev_actions=[],
    )

    toolkit_service.add_action(
        action=action2,
        next_actions=[(action3, 0.7), (action4, 0.9)],
        prev_actions=[(action1, 0.8)],
    )

    toolkit_service.add_action(
        action=action3,
        next_actions=[(action4, 0.7)],
        prev_actions=[(action1, 0.6), (action2, 0.7)],
    )

    toolkit_service.add_action(
        action=action4,
        next_actions=[],
        prev_actions=[(action2, 0.9), (action3, 0.7)],
    )

    # add tools with connections to actions
    toolkit_service.add_tool(tool=tool1, connected_actions=[(action1, 0.9)])
    toolkit_service.add_tool(tool=tool2, connected_actions=[(action2, 0.8)])
    toolkit_service.add_tool(tool=tool3, connected_actions=[(action3, 0.9)])
    toolkit_service.add_tool(tool=tool4, connected_actions=[(action4, 0.8)])

    toolkit: Toolkit = toolkit_service.get_toolkit()

    # verify initial graph structure
    assert len(toolkit.vertices()) == 8, "Graph should have 4 actions and 4 tools"
    assert len([n for n in toolkit.vertices() if toolkit.get_action(n)]) == 4, (
        "Should have 4 action vertices"
    )
    assert len([n for n in toolkit.vertices() if toolkit.get_tool(n)]) == 4, (
        "Should have 4 tool vertices"
    )

    # verify edge types and weights
    action_next_edges = [(u, v) for u, v in toolkit.edges() if toolkit.get_action(v)]
    tool_call_edges = [(u, v) for u, v in toolkit.edges() if toolkit.get_tool(v)]

    assert len(action_next_edges) == 5, "Should have 5 action-to-action edges"
    assert len(tool_call_edges) == 4, "Should have 4 action-to-tool edges"

    # verify all edge scores are within valid range
    assert all(0 <= toolkit.get_score(u, v) <= 1 for (u, v) in toolkit.edges()), (
        "All edge scores should be between 0 and 1"
    )

    # visualize the full graph
    toolkit_service.visualize(toolkit, "Full Toolkit Graph", show=True)
    plt.show(block=False)

    print("\nTesting recommendation with different parameters:")

    # test different scenarios and verify results
    test_cases = [
        {
            "actions": [action1],
            "threshold": 0.5,
            "hops": 0,
            "title": "Subgraph: Start from Action1, No hops, Threshold 0.5",
            "expected_vertices": {action1.id, tool1.id},  # action1 and its tool
            "expected_edges": 1,  # just the tool call edge
        },
        {
            "actions": [action1],
            "threshold": 0.5,
            "hops": 1,
            "title": "Subgraph: Start from Action1, 1 hop, Threshold 0.5",
            "expected_vertices": {
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
            "expected_vertices": {
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
            "expected_vertices": {
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
        subgraph = toolkit_service.recommend_subgraph(
            actions=case["actions"], threshold=case["threshold"], hops=case["hops"]
        )

        print(f"\nTest case {i + 1}:")
        print(f"Vertices: {subgraph.vertices()}")
        print(f"Edges: {subgraph.edges()}")

        # verify subgraph properties
        actual_vertices = set(subgraph.vertices())
        assert actual_vertices == case["expected_vertices"], (
            f"Test case {i + 1}: Expected vertices {case['expected_vertices']}, got {actual_vertices}"
        )

        assert len(subgraph.edges()) == case["expected_edges"], (
            f"Test case {i + 1}: Expected {case['expected_edges']} edges, "
            f"got {len(subgraph.edges())}"
        )

        # verify edge properties in subgraph
        assert all(subgraph.get_score(u, v) >= case["threshold"] for u, v in subgraph.edges()), (
            f"Test case {i + 1}: All edges should have score >= {case['threshold']}"
        )

        plt.figure(i + 2)
        toolkit_service.visualize(subgraph, case["title"], show=True)
        # plt.show(block=False)

    print("\nAll assertions passed! (press ctrl+c to exit)")
    plt.show()


if __name__ == "__main__":
    main()
