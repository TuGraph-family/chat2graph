from app.core.workflow.dataset_synthesis.model import TASK_LEVEL, GENERATOR_STRATEGY, SubTaskType,  LevelInfo, Row
from typing import List, Dict
import json

class QueryTaskSubtypes:
    # ------------------------------ L1: Simple Query Tasks (Single Node/Single Edge/Single-Step Reasoning) ------------------------------
    l1_tasks = [
        SubTaskType(
            level="L1",
            name="Entity Attribute and Label Query",
            desc="Core logic: Retrieve direct attributes (e.g., employee's department, product's production date) or node type labels of a single entity from the global database. The operation scope is 0-hop, focusing only on direct information of a single entity.",
            examples=[
                "What is the department of employee Zhang San?",
            ]
        ),
        SubTaskType(
            level="L1",
            name="Direct Relationship and Neighbor Query",
            desc="Core logic: Determine the 1-hop direct relationship (e.g., cooperation, supply) between two entities from the global database, or retrieve all 1-hop direct neighbors (e.g., team members, associated orders) of a single entity. The operation scope is 1-hop.",
            examples=[
                "Is there a 'cooperation' relationship between Company A and Company B?",
                "Who are the direct team members of team leader Wang Wu?"
            ]
        ),
        SubTaskType(
            level="L1",
            name="Simple Attribute Filtering",
            desc="Core logic: Filter nodes associated with a specified entity and meeting a single attribute condition (e.g., employee's tenure, product's inventory quantity) from the global database. The operation is based on 1-hop associations and single-condition filtering.",
            examples=[
                "Which products are in the same category as Product D and have an inventory > 100?"
            ]
        ),
        SubTaskType(
            level="L1",
            name="Single-Step Intuitive Reasoning Query",
            desc="Core logic: Derive results (e.g., an employee's direct supervisor, a product's storage warehouse) based on the 1-hop direct relationship of a single entity from the global database. The reasoning chain has only 1 step and does not require cross-multi-entity association.",
            examples=[
                "Who is the direct supervisor of employee Chen Qi?",
                "Which warehouse is Product D directly stored in?"
            ]
        )
    ]

    # ------------------------------ L2: Complex Query Tasks (Multi-Node/Multi-Edge/Multi-Step Reasoning, No Algorithms) ------------------------------
    l2_tasks = [
        SubTaskType(
            level="L2",
            name="Multi-Hop Relationship and Path Query",
            desc="Core logic: Query 2-hop and above association relationships (e.g., a friend's friend, a supplier's supplier) between two entities from the global database, or determine the reachability of multi-hop paths. The operation scope is ≥2 hops and requires cross-multi-entity association.",
            examples=[
                "Who are the friends of User A's friends?",
                "Can Supplier X be associated with Customer Y through the 'Supplier → Manufacturer → Customer' path?"
            ]
        ),
        SubTaskType(
            level="L2",
            name="Pattern-Based and Combined Filtering Query",
            desc="Core logic: Match small graph structure patterns of 'core entity → associated entity' from the global database, or filter associated nodes by combining multiple attribute conditions (e.g., region + employment time, production year + inventory). It requires integrating multiple conditions and multi-entity associations.",
            examples=[
                "Which R&D projects are managed by employees who work in the Beijing Branch and have been employed for more than 2 years?",
            ]
        ),
        # SubTaskType(
        #     level="L2",
        #     name="Small-Scale Aggregation Query",
        #     desc="Core logic: Perform simple aggregation calculations (e.g., quantity statistics, average calculation) on N-hop (N≥1) associated nodes of a specified entity from the global database. The aggregation scope focuses on the associated network of the entity, and no algorithm support is required.",
        #     examples=[
        #         "What is the total number of friends within 2 hops of User I?",
        #         "What is the average monthly sales volume of the downstream distributors of Product J?"
        #     ]
        # ), # TODO: 基于抽样的子图提出局部聚合的问题，会存在信息丢失，怎么解决？

        SubTaskType(
            level="L2",
            name="Multi-Step Chain Reasoning Query",
            desc="Core logic: Perform chain reasoning (e.g., an employee's supervisor's supervisor, a product supplier's partner manufacturer) along the multi-hop relationships (≥2 hops) of entities from the global database. The reasoning chain needs to cross multiple entities and does not require algorithm assistance.",
            examples=[
                "Who is the supervisor of Employee M's supervisor?",
                "Which manufacturer is the partner of Product N's supplier?"
            ]
        )
    ]

    # ------------------------------ L3: Simple Algorithm Application Tasks (Basic Graph Algorithms) ------------------------------
    l3_tasks = [
        SubTaskType(
            level="L3",
            name="Path Analysis",
            desc="Core logic: Call basic graph algorithms such as BFS and Dijkstra to calculate the shortest path between two entities (e.g., logistics distribution path, workplace reporting chain) from the global database. The algorithm logic is simple, and only a single algorithm is needed to obtain results.",
            examples=[
                "What is the shortest distribution path from Store A to Store B?",
                "How many hops are there in the shortest reporting chain from Employee Q to Employee R?"
            ]
        ),
        SubTaskType(
            level="L3",
            name="Local Topological Index Calculation",
            desc="Core logic: Call basic topological algorithms such as degree centrality and triangle counting to calculate topological indices (e.g., number of neighbor nodes, number of triangle relationships) within the associated network of a specified entity from the global database. The analysis scope focuses on the local associated network.",
            examples=[
                "How many triangle relationships are there in the friend circle (within 1 hop) of User W?",
                "What is the number of directly associated nodes (degree) of Product X?"
            ]
        ),
        SubTaskType(
            level="L3",
            name="Local Node Importance Ranking",
            desc="Core logic: Call algorithms such as simplified PageRank and degree centrality to perform Top-K importance ranking on the associated nodes of a specified entity (e.g., suppliers, employees, orders) from the global database. The analysis scope is limited to the set of associated nodes.",
            examples=[
                "Who are the top 3 most important suppliers among those associated with Product Z?",
                "Who are the top 5 employees with the highest degree centrality in the Technology Department?"
            ]
        ) # TODO: 这些基于子图提出的问题，答案可能不正确，怎么解决？
    ]

    # ------------------------------ L4: Complex Algorithm Application Tasks (Advanced Algorithms/Prediction/Anomaly Detection) ------------------------------
    l4_tasks = [
        SubTaskType(
            level="L4",
            name="Complex Pattern Matching",
            desc="Core logic: Call complex graph algorithms such as subgraph isomorphism to match complex subgraph structures with multiple attribute constraints (e.g., enterprise cooperation chains, workplace management chains) from the global database. It requires accurate identification of complex association patterns among multiple entities and multiple relationships.",
            examples=[
                "Which suppliers that cooperate with the government are among the subsidiaries controlled by companies with a registered capital exceeding 100 million?",
                "Which employees managed by supervisors who have been employed for more than 3 years are in charge of projects worth over 1 million?"
            ]
        ),
        SubTaskType(
            level="L4",
            name="Entity and Relationship Anomaly Detection",
            desc="Core logic: Call anomaly detection algorithms such as LOF and autoencoders to identify abnormal patterns (e.g., abnormal user behavior, abnormal equipment parameters, abnormal network topology) within the associated network of a specified entity from the global database. It requires mining implicit abnormal features.",
            examples=[
                "Does User A have abnormal login behavior of frequent IP switches across different regions?",
                "Do the operating parameters of Equipment B have abnormal fluctuations deviating from the historical baseline?"
            ]
        ),
        SubTaskType(
            level="L4",
            name="Prediction and Recommendation",
            desc="Core logic: Call machine learning algorithms such as link prediction and GNN to predict the future association relationships (e.g., business cooperation, social friends) of a specified entity from the global database, or recommend potential associated nodes. It requires modeling based on historical data.",
            examples=[
                "Which potential partners may Company CC add in the next 3 months?",
                "Which potential friends may User DD add?"
            ]
        ),
        SubTaskType(
            level="L4",
            name="Multi-Algorithm Hybrid Analysis",
            desc="Core logic: Combine 2 or more algorithms (e.g., clustering + PageRank, community detection + anomaly detection) to conduct step-by-step analysis on the associated network of a specified entity from the global database. It requires integrating results of multiple algorithms to obtain in-depth insights.",
            examples=[
                "First cluster the suppliers associated with Product Z, then find the core suppliers in each cluster. What is the result?",
                "First cluster user groups by interests, then find the top 3 influential users in each cluster. What is the result?"
            ]
        )
    ]

    L1 = LevelInfo(
        level="L1",
        name="Simple Query Tasks",
        desc="Level Core: Focuses on basic queries within 0-1 hops. The operation objects are 1-2 entities. The core is to retrieve direct attributes, determine 1-hop relationships, or perform single-step reasoning. No complex association logic or algorithm support is required, and the data source is the global database.",
        subtasks=l1_tasks
    )

    L2 = LevelInfo(
        level="L2",
        name="Complex Query Tasks (No Algorithms)",
        desc="Level Core: Focuses on complex queries with ≥2 hops. It needs to integrate multiple entities, multiple relationships, or multiple conditions, and supports pattern matching, aggregation calculation, and multi-step reasoning. The core is to obtain in-depth information through association logic, without calling graph algorithms. The data source is the global database.",
        subtasks=l2_tasks
    )

    L3 = LevelInfo(
        level="L3",
        name="Simple Algorithm Application Tasks",
        desc="Level Core: Based on the global database, call single, mature basic graph algorithms (e.g., BFS, degree centrality), focusing on path analysis, topological calculation, and importance ranking of local associated networks. Users do not need to understand algorithm details, and the core is to obtain structured insights through algorithms.",
        subtasks=l3_tasks
    )

    L4 = LevelInfo(
        level="L4",
        name="Complex Algorithm Application Tasks",
        desc="Level Core: Based on the global database, call complex graph algorithms, machine learning models, or multi-algorithm combinations, focusing on complex pattern matching, anomaly detection, prediction and recommendation, and in-depth analysis. The core is to mine implicit rules and future trends through advanced algorithms to obtain high-level business insights.",
        subtasks=l4_tasks
    )
    REGISTER_LIST = [L1, L2, L3]

SUBTYPES_MAP = {
    "query": [*QueryTaskSubtypes.REGISTER_LIST]
}

class GraphTaskTypesInfo:
    def __init__(self,
                 strategy: GENERATOR_STRATEGY = "query",
                 ):
        self.strategy = strategy
        self.tasks_info = SUBTYPES_MAP[strategy]
        self.count_info: Dict[str, Dict[str, int]] = {}
        
        for level_info in self.tasks_info:
            self.count_info[level_info.level] = {}
            for subtask in level_info.subtasks:
                self.count_info[level_info.level][subtask.name] = 0
    
    def update(self, rows: List[Row]):
        for row in rows:
            self.add(
                level=row.level,
                subtask=row.task_subtype
            )

    def add(self, level: TASK_LEVEL, subtask: str):
        if level in self.count_info and subtask in self.count_info[level]:
            self.count_info[level][subtask] += 1
        elif level in self.count_info:
            if "unknown" not in self.count_info[level]:
                self.count_info[level]["unknown"] = 0
            self.count_info[level]["unknown"] += 1
        else:
            print(f"[GraphTaskInfos]unknown level {level}")

    def get_tasks_info(self) -> str:
        tasks_info = ""
        for level_info in self.tasks_info:
            tasks_info += f"#### {level_info.level}: {level_info.name}\n"
            tasks_info += f"description: {level_info.desc}\n"
            tasks_info += f"subtask types: \n"
            for subtask in level_info.subtasks:
                tasks_info += f" - {subtask.name}: {subtask.desc}\n"
                tasks_info += f" - examples:\n"
  
                for idx, example in enumerate(subtask.examples, 1):
                    tasks_info += f"   {idx}. {example}\n"
                tasks_info += "\n"
            
            tasks_info += "---\n\n"
        
        return tasks_info

    def get_count_info(self) -> str:
        return json.dumps(self.count_info, indent=4, ensure_ascii=False)