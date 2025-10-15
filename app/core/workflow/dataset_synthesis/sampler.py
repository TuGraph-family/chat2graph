from abc import ABC, abstractmethod
import json
import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.toolkit.graph_db.graph_db import GraphDb


class SubGraphSampler(ABC):
    @abstractmethod
    def get_random_subgraph(
        self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int
    ) -> str: ...

class SimpleRandomSubGraphSampler(SubGraphSampler):
    def get_random_subgraph(
        self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int
    ) -> str:
        # 随机选择一个起始节点
        try:
            start_node = self._get_random_node(graph_db=graph_db)
            if not start_node:
                print("No nodes found.")
                raise ValueError("No nodes found.")
        except Exception as e:
            print(f"An unexpected error occurred while querying start node: {e}")
            raise e

        # 根据深度抽取子图
        subgraph_query = f"""
            MATCH (start)-[r*..{max_depth}]-(end)
            WHERE elementId(start) = $start_node_id
            RETURN start, r, end
        """
        try:
            with graph_db.conn.session() as session:
                result = session.run(subgraph_query, {"start_node_id": start_node.element_id})
                node_set = set()

                nodes = [start_node]
                node_set.add(start_node.element_id)
                relationships = []
                for record in result:
                    node = record["end"]
                    rel = record["r"]
                    relationships.append(rel)
                    if node.element_id not in node_set:
                        node_set.add(node.element_id)
                        nodes.append(node)

                print(
                    f"Successfully retrieved subgraph with {len(nodes)} nodes and {len(relationships)} relationships."
                )
        except Exception as e:
            print(f"An unexpected error occurred while retrieving subgraph: {e}")
            raise e
        subgraph_json = {
            "nodes": [
                {"id": node.id, "labels": list(node.labels), "properties": dict(node)}
                for node in nodes
            ],
            "relationships": [
                {
                    "id": rel.id,
                    "type": rel.type,
                    "start_node_id": rel.start_node.id,
                    "end_node_id": rel.end_node.id,
                    "properties": dict(rel),
                }
                for rels in relationships
                for rel in rels
            ],
        }
        return json.dumps(subgraph_json, indent=4)

    def _get_random_node(self, graph_db: GraphDb):
        with graph_db.conn.session() as session:
            # 执行 Cypher 查询
            result = session.run(
                """
                MATCH (n)
                WITH n, rand() AS random
                ORDER BY random
                LIMIT 1
                RETURN n
                """
            )
            # 获取查询结果
            node = result.single()
            if node:
                return node["n"]
            else:
                return None

class RandomWalkSampler(SubGraphSampler):
    def __init__(self):
        self.sampled_nodes: Set[str] = set()
        self.sample_counter = 0
        # 用于控制DFS/BFS倾向的参数，每次采样随机调整以增加多样性
        self.dfs_bias_range = (0.3, 0.7)

    def get_random_subgraph(
        self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int
    ) -> str:
        start_time = time.time()
        print("start sampling")
        nodes, relationships = self._get_random_subgraph(
            graph_db=graph_db, max_depth=max_depth, max_nodes=max_nodes, max_edges=max_edges
        )
        if nodes and relationships:
            subgraph_json = {
                "nodes": [
                    {
                        "elementId": node["node_id"],
                        "labels": node["labels"],
                        "properties": node["properties"],
                    }
                    for node in nodes
                ],
                "relationships": [
                    {
                        "elementId": rel["rel_id"],
                        "type": rel["rel_type"],
                        "start_node_elementId": rel["start_node_id"],
                        "end_node_elementId": rel["end_node_id"],
                        "properties": rel["properties"],
                    }
                    for rel in relationships
                ],
            }
            elapsed = time.time() - start_time
            print(
                f"Successfully retrieved subgraph with {len(nodes)} nodes and {len(relationships)} relationships. elapse: {elapsed: .2f}"
            )
            info = [node["node_id"] for node in nodes[:3]]
            print(f"first 3 nodes id: {info}")
            return json.dumps(subgraph_json, indent=4)
        else:
            return ""

    def _get_available_start_node(self, graph_db: GraphDb) -> str:
        """获取一个未被采样过的起始节点"""
        # 构建排除已采样节点的条件
        exclude_clause = ""
        params = {}
        if self.sampled_nodes:
            exclude_clause = "WHERE NOT elementId(n) IN $excluded_nodes"
            params["excluded_nodes"] = list(self.sampled_nodes)

        # 随机选择一个可用节点
        query = f"""
        MATCH (n)
        {exclude_clause}
        WITH n, rand() AS r
        ORDER BY r
        LIMIT 1
        RETURN elementId(n) AS node_id
        """

        try:
            with graph_db.conn.session() as session:
                result = session.run(query, params)
                record = result.single()
                if record.get("node_id", "") != "":
                    return record["node_id"]
                self.sampled_nodes.clear()
                result = session.run(query)
                return result.single()["node_id"]
        except Exception as e:
            print(f"[_get_available_start_node] failed: {str(e)}")
            return ""

    def _random_walk_step(
        self,
        graph_db: GraphDb,
        current_nodes: Set[str],
        depth: int,
        max_depth: int,
        max_nodes: int,
        max_edges: int,
        dfs_bias: float,
    ) -> Tuple[Set[int], Set[int]]:
        """执行一步随机游走，返回新的节点和关系"""
        if not current_nodes or depth >= max_depth:
            return set(), set()

        # 构建当前节点参数
        params = {
            "current_nodes": list(current_nodes),
            "dfs_bias": dfs_bias,
            "max_possible": min(
                max_nodes - len(self.current_sample_nodes),
                max_edges - len(self.current_sample_edges),
            ),
        }

        # 纯Cypher实现的随机游走步骤，结合DFS和BFS特性
        query = """
        UNWIND $current_nodes AS current_id
        MATCH (current)-[r]-(neighbor)
        WHERE elementId(current) = current_id
        
        WITH current, r, neighbor,
             rand() AS random_val,
             (1.0 / (size([n IN $current_nodes WHERE n = elementId(current)]) + 1)) * $dfs_bias +
             (CASE WHEN elementId(neighbor) IN $current_nodes THEN 0 ELSE 1 END) * (1 - $dfs_bias) AS weight
        
        ORDER BY weight DESC, random_val
        LIMIT $max_possible
        
        RETURN DISTINCT elementId(neighbor) AS node_id, elementId(r) AS rel_id
        """
        try:
            with graph_db.conn.session() as session:
                result = session.run(query, params)
                new_nodes = set()
                new_rels = set()
                for record in result:
                    if record.get("node_id", "") != "":
                        new_nodes.add(record["node_id"])
                    if record.get("rel_id", "") != "":
                        new_rels.add(record["rel_id"])
                return new_nodes, new_rels
        except Exception as e:
            print(f"[_random_walk_step] failed: {str(e)}")
            return new_nodes, new_rels

    def _get_random_subgraph(
        self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        生成随机子图的主方法

        :param graph_db: GraphDb实例，用于执行Cypher查询
        :param max_depth: 最大游走深度
        :param max_nodes: 最大节点数量
        :param max_edges: 最大边数量
        :return: 子图数据的JSON字符串，包含nodes和relationships
        """
        # 参数验证
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if max_nodes < 1:
            raise ValueError("max_nodes must be at least 1")
        if max_edges < 1:
            raise ValueError("max_edges must be at least 1")

        self.sample_counter += 1

        # 选择起始节点
        start_node = self._get_available_start_node(graph_db)
        if not start_node or len(start_node) == "":
            raise Exception("[_get_random_subgraph] Cann't find start_node")

        # 初始化采样集合
        self.current_sample_nodes = {start_node}
        self.current_sample_edges: Set[int] = set()
        current_frontier = {start_node}
        dfs_bias = random.uniform(*self.dfs_bias_range)  # 随机DFS偏向，增加多样性

        # 执行多步随机游走
        for depth in range(max_depth):
            # 执行一步游走
            new_nodes, new_edges = self._random_walk_step(
                graph_db, current_frontier, depth, max_depth, max_nodes, max_edges, dfs_bias
            )

            # 更新采样集合
            nodes_to_add = new_nodes - self.current_sample_nodes
            edges_to_add = new_edges - self.current_sample_edges

            # 检查是否达到限制
            remaining_node_slots = max_nodes - len(self.current_sample_nodes)
            remaining_edge_slots = max_edges - len(self.current_sample_edges)

            if remaining_node_slots <= 0 and remaining_edge_slots <= 0:
                break

            # 添加新节点，不超过最大限制
            if nodes_to_add and remaining_node_slots > 0:
                nodes_to_add = list(nodes_to_add)[:remaining_node_slots]
                self.current_sample_nodes.update(nodes_to_add)
                current_frontier = set(nodes_to_add)  # 下一轮从新节点开始

            # 添加新边，不超过最大限制
            if new_edges and remaining_edge_slots > 0:
                edges_to_add = list(edges_to_add)[:remaining_edge_slots]
                self.current_sample_edges.update(edges_to_add)

            # 如果没有新节点和边，提前结束
            if not nodes_to_add and not edges_to_add:
                break

        # 记录已采样节点，确保后续采样多样性
        self.sampled_nodes.update(self.current_sample_nodes)

        try:
            with graph_db.conn.session() as session:
                # 1. 若节点已满，边未满：基于已选节点补充边
                remaining_edges = max_edges - len(self.current_sample_edges)
                if len(self.current_sample_nodes) >= max_nodes and remaining_edges > 0:
                    # 查询已选节点之间未被采样的边
                    query = """
                    UNWIND $node_ids AS nid
                    MATCH (a)-[r]-(b)
                    WHERE elementId(a) IN $node_ids 
                        AND elementId(b) IN $node_ids
                        AND NOT elementId(r) IN $edge_ids
                    WITH r ORDER BY rand()  
                    LIMIT $remaining  
                    RETURN elementId(r) AS rel_id
                    """

                    result = session.run(
                        query,
                        {
                            "node_ids": list(self.current_sample_nodes),
                            "edge_ids": list(self.current_sample_edges),
                            "remaining": remaining_edges,
                        },
                    )
                    supply_edges = [record["rel_id"] for record in result]
                    self.current_sample_edges.update(supply_edges)

                # 2. 若边已满，节点未满：基于已选边补充节点
                remaining_nodes = max_nodes - len(self.current_sample_nodes)
                if len(self.current_sample_edges) >= max_edges and remaining_nodes > 0:
                    # 查询已选边关联的未被采样的邻居节点
                    query = """
                    UNWIND $edge_ids AS rid
                    MATCH ()-[r]->(m) WHERE elementId(r) = rid
                    WITH DISTINCT m  
                    WHERE NOT elementId(m) IN $node_ids
                    WITH m ORDER BY rand()  
                    LIMIT $remaining  
                    RETURN elementId(m) AS node_id
                    """
                    result = session.run(
                        query,
                        {
                            "edge_ids": list(self.current_sample_edges),
                            "node_ids": list(self.current_sample_nodes),
                            "remaining": remaining_nodes,
                        },
                    )
                    supply_nodes = [record["node_id"] for record in result]
                    self.current_sample_nodes.update(supply_nodes)
                    # 同步记录已采样节点
                    self.sampled_nodes.update(supply_nodes)
        except Exception as e:
            print(f"[_get_random_subgraph] supply failed: {str(e)}")
            return [], []

        # 获取节点详细信息
        nodes_query = """
        UNWIND $node_ids AS id
        MATCH (n) WHERE elementId(n) = id
        RETURN elementId(n) AS node_id, labels(n) AS labels, properties(n) AS properties
        """

        # 获取关系详细信息
        rels_query = """
        UNWIND $rel_ids AS id
        MATCH ()-[r]->() WHERE elementId(r) = id
        RETURN elementId(r) AS rel_id, type(r) AS rel_type,
               elementId(startNode(r)) AS start_node_id,
               elementId(endNode(r)) AS end_node_id,
               properties(r) AS properties
        """

        try:
            with graph_db.conn.session() as session:
                nodes_result = session.run(
                    nodes_query, {"node_ids": list(self.current_sample_nodes)}
                )
                nodes = list(nodes_result)
                rels_result = session.run(rels_query, {"rel_ids": list(self.current_sample_edges)})
                rels = list(rels_result)
        except Exception as e:
            print(f"[_get_random_subgraph] failed: {str(e)}")
            return [], []

        return nodes, rels

class RandomSubgraphSampler:
    def __init__(self):
        # 使用 elementId()（字符串）作为标识
        self.sampled_node_ids: Set[str] = set()
        self.recent_sample_nodes: List[str] = []
        self.last_subgraph: Dict[str, Any] = {}

    def _normalize_params(self, params: Optional[Dict]):
        """确保数值参数为 int，集合转为 list，避免 float/int 混淆导致 driver 问题"""
        if not params:
            return {}
        norm = {}
        for k, v in params.items():
            if isinstance(v, float) and v.is_integer():
                norm[k] = int(v)
            elif isinstance(v, set | tuple):
                norm[k] = list(v)
            else:
                norm[k] = v
        return norm

    def _run(self, graph_db, cypher: str, params: Dict = None):
        """执行 cypher 并返回 list(dict) 结果。保证 params 类型安全。"""
        params = self._normalize_params(params)
        with graph_db.conn.session() as session:
            result = session.run(cypher, params)
            # driver 返回的 record 可能不能直接转 dict（取决 driver），
            # 这里尽量将每条 record 转成 python 原生结构（节点/关系对象由 driver 决定）
            rows = [dict(r) for r in result]
        return rows

    def _pick_random_seed(self, graph_db, excluded: Set[str], max_tries: int = 10) -> str:
        """
        用 elementId 选随机起点，优先避开 excluded（字符串列表）
        返回 elementId(n) 的字符串
        """
        excluded_list = list(excluded) if excluded else []
        for attempt in range(max_tries):
            if excluded_list:
                q = """
                MATCH (n)
                WHERE NOT elementId(n) IN $excluded
                RETURN elementId(n) AS eid
                ORDER BY rand()
                LIMIT 1
                """
                rows = self._run(graph_db, q, {"excluded": excluded_list})
            else:
                q = "MATCH (n) RETURN elementId(n) AS eid ORDER BY rand() LIMIT 1"
                rows = self._run(graph_db, q, {})
            if rows:
                return rows[0]["eid"]
        # 放宽：从全图随机挑一个
        q = "MATCH (n) RETURN elementId(n) AS eid ORDER BY rand() LIMIT 1"
        rows = self._run(graph_db, q, {})
        if rows:
            return rows[0]["eid"]
        raise RuntimeError("Graph empty: cannot pick seed node")

    def get_random_subgraph(self, graph_db, max_depth: int, max_nodes: int, max_edges: int) -> str:
        # 参数防御
        if max_nodes <= 0:
            raise ValueError("max_nodes must be > 0")
        if max_depth < 0:
            raise ValueError("max_depth must be >= 0")

        # 强制整型，避免 float 导致 driver/内部出错
        max_depth = int(max_depth)
        max_nodes = int(max_nodes)
        max_edges = int(max_edges)

        sub_nodes: Set[str] = set()
        sub_rels: Set[str] = set()

        excluded_for_seed = set(self.sampled_node_ids)
        seed_eid = self._pick_random_seed(graph_db, excluded_for_seed)
        sub_nodes.add(seed_eid)
        frontier = {seed_eid}
        depth = 0

        while frontier and depth < max_depth and len(sub_nodes) < max_nodes and len(sub_rels) < max_edges:
            depth += 1
            new_frontier = set()
            for eid in list(frontier):
                if len(sub_nodes) >= max_nodes or len(sub_rels) >= max_edges:
                    break

                remaining_nodes = max_nodes - len(sub_nodes)
                remaining_edges = max_edges - len(sub_rels)
                k = int(min(remaining_nodes, 5))  # 每个节点最多向外扩展 k 个邻居（int 保证）
                if k <= 0:
                    continue

                # 找与当前节点相连的邻居（基于 elementId）
                q = """
                MATCH (n)-[r]-(m)
                WHERE elementId(n) = $eid AND NOT elementId(m) IN $excluded_nodes
                RETURN elementId(m) AS mid, elementId(r) AS rid
                ORDER BY rand()
                LIMIT $limit
                """
                excluded_nodes = list(sub_nodes.union(self.sampled_node_ids))
                rows = self._run(graph_db, q, {"eid": eid, "excluded_nodes": excluded_nodes, "limit": k})

                # 若没有结果（图稀疏或 excluded 过多），放宽条件（只排除当前 sub_nodes）
                if not rows:
                    q2 = """
                    MATCH (n)-[r]-(m)
                    WHERE elementId(n) = $eid AND NOT elementId(m) IN $sub_nodes
                    RETURN elementId(m) AS mid, elementId(r) AS rid
                    ORDER BY rand()
                    LIMIT $limit
                    """
                    rows = self._run(graph_db, q2, {"eid": eid, "sub_nodes": list(sub_nodes), "limit": k})

                for r in rows:
                    if len(sub_nodes) >= max_nodes or len(sub_rels) >= max_edges:
                        break
                    mid = r["mid"]
                    rid = r["rid"]
                    # rid 与 mid 在这里都是字符串（elementId）
                    if mid not in sub_nodes:
                        if len(sub_nodes) < max_nodes:
                            sub_nodes.add(mid)
                            new_frontier.add(mid)
                    # 边数控制（尽量用关系 elementId）
                    if rid not in sub_rels and len(sub_rels) < max_edges:
                        sub_rels.add(rid)

            frontier = new_frontier

        # 如果只有一个节点且允许的话，尝试抓取一些与 seed 相连的边（补充边/邻居）
        if len(sub_nodes) == 1 and max_edges > 0:
            remaining_edges = max_edges - len(sub_rels)
            if remaining_edges > 0:
                q = """
                MATCH (n)-[r]-(m)
                WHERE elementId(n) = $eid
                RETURN elementId(m) AS mid, elementId(r) AS rid
                ORDER BY rand()
                LIMIT $limit
                """
                rows = self._run(graph_db, q, {"eid": seed_eid, "limit": remaining_edges})
                for r in rows:
                    if len(sub_nodes) >= max_nodes or len(sub_rels) >= max_edges:
                        break
                    mid = r["mid"]
                    rid = r["rid"]
                    if mid not in sub_nodes and len(sub_nodes) < max_nodes:
                        sub_nodes.add(mid)
                    if rid not in sub_rels and len(sub_rels) < max_edges:
                        sub_rels.add(rid)

        # 记录到 sampled_node_ids 用于后续避免重复（字符串 ids）
        for nid in sub_nodes:
            self.sampled_node_ids.add(nid)
        self.recent_sample_nodes = list(sub_nodes)

        # 最终的诱导子图查询（使用 elementId 判断）
        final_query = """
        WITH $node_ids AS ids
        MATCH (n)
        WHERE elementId(n) IN ids
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE elementId(m) IN ids
        RETURN collect(DISTINCT n) AS nodes, collect(DISTINCT r) AS relationships
        """

        final_rows = self._run(graph_db, final_query, {"node_ids": list(sub_nodes)})

        nodes_out = []
        rels_out = []
        if final_rows:
            row = final_rows[0]
            nodes_out = row.get("nodes", [])
            rels_out = row.get("relationships", [])

        self.last_subgraph = {
            "node_ids": list(sub_nodes),
            "rel_ids": list(sub_rels),
            "nodes": nodes_out,
            "relationships": rels_out,
            "final_query": final_query,
        }

        return json.dumps(self.last_subgraph, indent=2, ensure_ascii=False)