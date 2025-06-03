# Toolkit

## 1. Introduction

The Toolkit module is a core component of Chat2Graph, primarily responsible for recommending specific execution instructions to `Operator` within the framework and enabling interaction with the external world. It achieves this by meticulously managing a directed graph composed of "Actions" and "Tools" — the `Toolkit`. This graph not only precisely defines the invocation relationships between different tools but also clarifies their potential execution sequences, thereby expanding the operational capabilities of `Operator`.

This module addresses tool invocation challenges through several innovations. First, it implements an advanced tool management mechanism: by constructing a directed graph containing Actions & Tools, it clearly describes dependency and transition relationships between tool invocations, far surpassing traditional flat tool lists. Based on this graph structure, the system can more intelligently recommend contextually appropriate Tools and related "Actions" to large language models (LLMs), significantly improving recommendation accuracy. Meanwhile, the graph's precision effectively constrains the LLM's tool selection scope, reducing uncertainty and potential error rates in tool invocation. For developers, Toolkit provides a unified tool registration and recommendation mechanism, enabling easy reuse of Tools and Actions, thus simplifying development workflows. Future enhancements will include support for MCP (Model Context Protocol) and offline learning capabilities to strengthen `ToolkitService` recommendations through reinforcement learning.

Key features of the Toolkit module include:
1. Support for Tool definition and registration, compatible with LLM function calling patterns.
2. Ability to define Actions, where each Action can contain a set of available Tools and links to subsequent potential Actions.
3. Core Toolkit component responsible for overall graph construction and management.
4. Service-oriented access via `ToolkitService`, with convenient SDK interfaces provided through `ToolkitWrapper` for upper-layer applications.

The Toolkit is shared across the entire system, making its Actions and Tools reusable.

## 2. Design

### 2.1. **Tool Graph Design**

`Toolkit` employs a directed graph structure to organize Tools and Actions. Nodes in the graph are primarily `Actions`, where each `Action` node can associate with a group of `Tools`, representing executable operations under that Action. Meanwhile, `Actions` point to subsequent possible `Action` nodes through their `next_action_ids` attribute. In this graph, `Actions` are connected by weighted `Next` edges, indicating sequential relationships and their association strengths; while `Actions` and their associated `Tools` are connected by weighted `Call` edges, representing logical relationships and invocation probabilities. This graph structure clearly defines different task execution phases (i.e., `Actions`), tools available at each phase (i.e., `Tools`), and potential transition paths between them, providing clear workflow guidance for task execution.

1. `Tool` represents an independent, executable tool. Each Tool contains its name, functional description, input parameter JSON Schema definition, and concrete execution logic. In `Toolkit`, `Tools` are basic execution units invoked by `Actions`. `Tools` can be called by `Reasoner`. Additionally, they support module services (e.g., `GraphDbService`) defined via `app.core.reasoner.injection_mapping` as tool parameters, automatically injected during invocation (i.e., you don't need to declare service module parameters in docstrings since `Reasoner` automatically detects and imports corresponding modules during tool calls), enhancing flexibility and functionality.

2. `Action` represents a state or decision point for LLMs during task execution, serving as core nodes in the `Toolkit` graph. `Action` descriptions help LLMs understand their represented intents and functionalities. An `Action` can associate with one or more `Tools`, indicating potential tool invocations when executing that Action.

3. `Toolkit` organizes and manages the directed graph composed of multiple `Action` and `Tool` nodes. It's not just a simple collection of tools but, more importantly, clearly expresses invocation logic and task flows. In the graph, `Actions` are connected by `Next` edges defining execution sequences; `Actions` and `Tools` are connected by `Call` edges defining invocation relationships.

4. `ToolkitService` manages `Toolkit` instances and recommends appropriate `Actions` and `Tools` to LLMs based on current context.

  ![](../../en/img/toolkit.png)

  This graph-based Toolkit mechanism offers significant advantages. First, it enables context-aware tool recommendations: the system can more precisely recommend available `Tools` under the current `Action` or potential next `Actions` based on the current node's position in the graph, far more intelligent and efficient than providing a flat, context-free tool list. Second, the predefined graph structure effectively narrows the LLM's search space when selecting tools or deciding next actions, significantly reducing randomness and uncertainty, thereby improving invocation accuracy and overall task execution efficiency. Finally, this structured approach makes complex workflow modeling more natural and intuitive, clearly expressing multi-step processes with dependencies or conditional tool invocation flows.

### 2.2. **Toolkit Implementation**

1. **Initial Configuration**: The system presets `Actions`, `Tools`, and `Operator`-bound `Action` collections via YAML configuration. The operational tools for the graph database have been integrated into the system as built-in capabilities, and can be registered through the [GraphDB](../graph_db/graph-db.md) service. Additionally, dynamic tool registration capability is under development.

2. **Tool Recommendation**: Based on `Operator`-bound `Action` collections, `ToolkitService` performs graph exploration in the Toolkit. It discovers `Actions` and `Tools` related to the current `Action` and offers them as recommendations. Recommendation scope (e.g., exploration depth or association strength) can be controlled via threshold configuration and graph traversal hops.

![](../../en/img/tool-recommendation.png)

3. **Tool Calling**: `Reasoner` (typically combined with LLM decision-making) selects the most suitable `Tool` from `ToolkitService` recommendations. Upon selection, `Reasoner` executes the `Tool` and obtains results for subsequent task processing.

![](../../en/img/reasoner-enhancement.png)    

4. **Toolkit Optimization**: Toolkit capabilities continue to improve, such as one-click toolset registration and graph optimization via reinforcement learning.

![](../../en/img/toolkit-enhancement.png)

### 2.3. **API**

#### 2.3.1. Toolkit API

The `Toolkit` class inherits from `Graph`, specifically designed to build and manage directed graphs of `Actions` and `Tools`.

| Method Signature                                      | Description                                                                                                             |
| :--------------------------------------------------------------- |:---------------------------------------------------------------------------------------------------------------|
| `add_vertex(self, id, **properties) -> None`                     | Adds a vertex (`Action` or `Tool`) to the graph. The `properties` dictionary should contain a `data` key with `Action` or `Tool` object as value. Based on object type, stores it in corresponding internal dictionaries. |
| `vertices_data(self) -> List[Tuple[str, Dict[str, Union[Action, Tool]]]]` | Retrieves all vertices and their associated data (`Action` or `Tool` objects) in the Toolkit. Returns a list of tuples, each containing a vertex ID and a dictionary with its data.                                       |
| `update(self, other: Graph) -> None`                             | Updates the current graph using vertices and edges from another `Toolkit` instance (`other`). Existing vertices/edges aren't duplicated; new `Actions`, `Tools`, edges, and their scores from `other` are added to the current graph. |
| `subgraph(self, ids: List[str]) -> "Toolkit"`                    | Creates and returns a new `Toolkit` instance as a subgraph of the original, containing specified vertices (via `ids` list) and their connecting edges with associated data.                                   |
| `remove_vertex(self, id: str) -> None`                           | Removes a vertex and its associated `Action` or `Tool` from the graph. If removing an `Action` that's the sole predecessor for any `Tool` successor nodes, those `Tools` are also removed.     |
| `get_action(self, id: str) -> Optional[Action]`                  | Retrieves an `Action` object by vertex ID. Returns `None` if ID doesn't exist or doesn't correspond to an `Action`.                                                   |
| `get_tool(self, id: str) -> Optional[Tool]`                      | Retrieves a `Tool` object by vertex ID. Returns `None` if ID doesn't exist or doesn't correspond to a `Tool`.                                                       |
| `get_score(self, u: str, v: str) -> float`                       | Gets the edge score connecting vertices `u` and `v`. Returns 1.0 by default if edge doesn't exist.                                                                        |
| `set_score(self, u: str, v: str, score: float) -> None`          | Sets the edge score connecting vertices `u` and `v`.                                                                                        |

#### 2.3.2. Toolkit Service API

`ToolkitService` is a singleton service managing `Toolkit` instances, providing tool/action registration, recommendation, and visualization functionalities.

| Method Signature                                                                 | Description                                                                                                                                                                                 |
| :------------------------------------------------------------------------------------------ |:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `get_toolkit(self) -> Toolkit`                                                              | Returns the `Toolkit` instance currently managed by the service.                                                                                                                                                            |
| `add_tool(self, tool: Tool, connected_actions: List[Tuple[Action, float]])`                 | Adds a `Tool` to the Toolkit. `tool` is the Tool object to add, `connected_actions` is a list of `Action` objects invoking this tool with their associated scores (indicating connection strength). Prints warnings if `Action` doesn't exist in the graph. Also warns and removes the tool if no `Action` connections exist.                        |
| `add_action(self, action: Action, next_actions: List[Tuple[Action, float]], prev_actions: List[Tuple[Action, float]]) -> None` | Adds an `Action` to the Toolkit. `action` is the Action object to add, `next_actions` and `prev_actions` are lists of subsequent/preceding `Actions` with their connection scores.                                                                              |
| `get_action(self, id: str, action_id: str) -> Action`                                       | Retrieves an `Action` object by `action_id` from the Toolkit. Raises `ValueError` if not found. (Note: `id` parameter is unused in current implementation)                                                                                                  |
| `remove_tool(self, id: str, tool_id: str)`                                                  | Removes a `Tool` by `tool_id` from the Toolkit. (Note: `id` parameter is unused in current implementation)                                                                                                                              |
| `remove_action(self, id: str, action_id: str)`                                              | Removes an `Action` by `action_id` from the Toolkit. (Note: `id` parameter is unused in current implementation)                                                                                                                          |
| `recommend_subgraph(self, actions: List[Action], threshold: float = 0.5, hops: int = 0) -> Toolkit` | Core recommendation engine method. Based on input `Action` list, performs weighted BFS within specified `hops` to find related `Actions`, then associates `Tools` invoked by these `Actions`. All connection scores must meet or exceed `threshold`. Returns a subgraph (`Toolkit`) containing these related `Actions` and `Tools`.      |
| `recommend_tools_actions(self, actions: List[Action], threshold: float = 0.5, hops: int = 0) -> Tuple[List[Tool], List[Action]]` | Based on `recommend_subgraph` results, extracts recommended `Tools` and `Actions` from the subgraph, returning a tuple containing a `Tool` list and an `Action` list.                                                                                    |
| `visualize(self, graph: Toolkit, title: str, show=False)`                                   | Visualizes the given `Toolkit` graph (`graph`). `Action` and `Tool` nodes are displayed with different colors/shapes; edges are differentiated by type (Action-Action or Action-Tool) with displayed connection scores. `title` sets the chart title; `show` determines whether to display the image immediately. Returns a `matplotlib.pyplot.Figure` object. |

## 3. Examples

* `Toolkit` `Action` and `Tool` registration: See sample code in `test/example/run_toolkit.py`.
* `ToolkitService` recommending `Actions` and `Tools` to `Operator`: See `test/example/run_operator.py`.