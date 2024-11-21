import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.tool.tool_resource import Query
from app.toolkit.toolkit import Toolkit, ToolkitGraphType


def visualize_toolkit_graph(graph: nx.DiGraph, title: str):
    """Visualize the toolkit graph with different colors for actions and tools.

    Args:
        graph: The graph to visualize
        title: Title for the plot
    """
    plt.figure(figsize=(12, 8))

    # Get node positions using spring layout with larger distance and more iterations
    pos = nx.spring_layout(
        graph, k=2, iterations=200
    )  # increase k and iterations for better layout

    # Draw nodes
    action_nodes = [
        n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.ACTION
    ]
    tool_nodes = [
        n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.TOOL
    ]

    # Draw action nodes in blue
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=action_nodes,
        node_color="lightblue",
        node_size=2000,
        node_shape="o",
    )

    # Draw tool nodes in green
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=tool_nodes,
        node_color="lightgreen",
        node_size=1500,
        node_shape="s",
    )

    # Draw edges with different colors and styles for different types
    next_edges = [
        (u, v)
        for (u, v, d) in graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
    ]
    call_edges = [
        (u, v)
        for (u, v, d) in graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_CALL_TOOL
    ]

    # Draw action-to-action edges in blue with curved arrows
    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=next_edges,
        edge_color="blue",
        arrows=True,
        arrowsize=35,
        width=2,
    )

    # Draw action-to-tool edges in green with different curve style
    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=call_edges,
        edge_color="green",
        arrows=True,
        arrowsize=35,
        width=1.5,
    )

    # Add edge labels (scores) with adjusted positions for curved edges
    edge_labels = {(u, v): f"{d['score']:.2f}" for (u, v, d) in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels,
        font_size=8,
        label_pos=0.5,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
    )

    # Add node labels - handle both Action and Tool nodes
    node_labels = {}
    for n, d in graph.nodes(data=True):
        if d["type"] == ToolkitGraphType.ACTION:
            node_labels[n] = d["data"].id
        elif d["type"] == ToolkitGraphType.TOOL:
            node_labels[n] = d["data"].id

    # Draw labels with white background for better visibility
    nx.draw_networkx_labels(
        graph,
        pos,
        node_labels,
        font_size=8,
        # bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
    )

    plt.title(title)
    plt.axis("off")

    # Add a legend

    legend_elements = [
        Line2D([0], [0], color="blue", label="Action→Action"),
        Line2D([0], [0], color="green", label="Action→Tool"),
        plt.scatter([0], [0], color="lightblue", s=100, label="Action"),
        plt.scatter([0], [0], color="lightgreen", marker="s", s=100, label="Tool"),
    ]
    plt.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1, 1))

    plt.tight_layout()
    return plt.gcf()


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
    tool1: Tool = Query(tool_id="tool1")
    tool2: Tool = Query(tool_id="tool2")
    tool3: Tool = Query(tool_id="tool3")
    tool4: Tool = Query(tool_id="tool4")

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
    assert len(toolkit.toolkit_graph.nodes()) == 8, (
        "Graph should have 4 actions and 4 tools"
    )
    assert (
        len([
            n
            for n, d in toolkit.toolkit_graph.nodes(data=True)
            if d["type"] == ToolkitGraphType.ACTION
        ])
        == 4
    ), "Should have 4 action nodes"
    assert (
        len([
            n
            for n, d in toolkit.toolkit_graph.nodes(data=True)
            if d["type"] == ToolkitGraphType.TOOL
        ])
        == 4
    ), "Should have 4 tool nodes"

    # verify edge types and weights
    action_next_edges = [
        (u, v, d)
        for u, v, d in toolkit.toolkit_graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
    ]
    tool_call_edges = [
        (u, v, d)
        for u, v, d in toolkit.toolkit_graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_CALL_TOOL
    ]

    assert len(action_next_edges) == 5, "Should have 5 action-to-action edges"
    assert len(tool_call_edges) == 4, "Should have 4 action-to-tool edges"

    # verify all edge scores are within valid range
    assert all(
        0 <= d["score"] <= 1 for _, _, d in toolkit.toolkit_graph.edges(data=True)
    ), "All edge scores should be between 0 and 1"

    # visualize the full graph
    visualize_toolkit_graph(toolkit.toolkit_graph, "Full Toolkit Graph")
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
        subgraph = await toolkit.recommend_toolkit_subgraph(
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
        visualize_toolkit_graph(subgraph, case["title"])
        # plt.show(block=False)

    print("\nAll assertions passed! (press ctrl+c to exit)")
    plt.show()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
