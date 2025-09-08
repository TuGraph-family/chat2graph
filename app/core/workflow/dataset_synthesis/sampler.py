from abc import ABC, abstractmethod
from app.core.toolkit.graph_db.graph_db import GraphDb
from typing import Optional, List, Dict, Tuple, Set
import json
import time
import random


class SubGraphSampler(ABC):
    @abstractmethod
    def get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> str:
        ...

class SimpleRandomSubGraphSampler(SubGraphSampler):
    def get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> str:
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
                    
                print(f"Successfully retrieved subgraph with {len(nodes)} nodes and {len(relationships)} relationships.")
        except Exception as e:
            print(f"An unexpected error occurred while retrieving subgraph: {e}")
            raise e
        subgraph_json = {
            "nodes": [{"id": node.id, "labels": list(node.labels), "properties": dict(node)} for node in nodes],
            "relationships": [{"id": rel.id, "type": rel.type, "start_node_id": rel.start_node.id, "end_node_id": rel.end_node.id, "properties": dict(rel)} for rels in relationships for rel in rels]
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

class EnhancedSubgraphSampler(SubGraphSampler):
    def get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> str:
        self.graph_db: GraphDb = graph_db
        print(f"start sampling...")
        start_time = time.time()
        nodes, relationships = self._get_random_subgraph(target_size=max_nodes)
        elapsed = time.time() - start_time
        subgraph_json = {
            "nodes": [{"id": node["node_id"], "labels": node["labels"], "properties": node["properties"]} for node in nodes],
            "relationships": [{"id": rel["rel_id"], "type": rel["rel_type"], "start_node_id": rel["start_node_id"], "end_node_id": rel["end_node_id"], "properties": rel["properties"]} for rel in relationships]
        }
        print(f"Successfully retrieved subgraph with {len(nodes)} nodes and {len(relationships)} relationships. elapse: {elapsed: .2f}")
        info = [node["node_id"] for node in nodes[:3]]
        print(f"first 3 nodes id: {info}")
        return json.dumps(subgraph_json, indent=4)
    
    def _count_total_nodes(self, label: Optional[str] = None) -> int:
        """统计符合条件的总节点数，用于抽样概率计算
        
        :param label: 节点标签，None表示所有节点
        :return: 节点总数
        """
        query = f"""
        MATCH (n{':' + label if label else ''})
        RETURN count(n) AS total
        """
        
        try:
            with self.graph_db.conn.session() as session:
                result = session.run(query)
                return result.single()["total"]
        except Exception as e:
            print(f"failed while statistic: {str(e)}")
            return 0
    
    def _random_seed_nodes(self, label: Optional[str] = None, count: int = 5) -> List[Dict]:
        """随机选择种子节点
        
        :param label: 节点标签
        :param count: 种子节点数量
        :return: 种子节点列表
        """
        if count <= 0:
            return []
            
        query = f"""
        MATCH (n{':' + label if label else ''})
        WITH n, rand() AS r
        ORDER BY r
        LIMIT $count
        RETURN elementId(n) AS node_id, labels(n) AS labels, properties(n) AS properties
        """
        
        try:
            with self.graph_db.conn.session() as session:
                result = session.run(query, count=count)
                return [record.data() for record in result]
        except Exception as e:
            print(f"failed while get seed node: {str(e)}")
            return []
    
    def _smart_neighbor_selection(self, 
                                 node_ids: List[int], 
                                 existing_nodes: set, 
                                 limit: int,
                                 prefer_connected: float = 0.7) -> List[Dict]:
        """智能选择邻居节点，优先选择能增强连通性的节点
        
        :param node_ids: 基准节点ID列表
        :param existing_nodes: 已有的节点集合
        :param limit: 最大选择数量
        :param prefer_connected: 优先选择与已有节点连接的概率(0-1)
        :return: 选中的邻居节点列表
        """
        if not node_ids or limit <= 0:
            return []
            
        # 混合策略：部分邻居来自与已有节点的连接，部分来自随机
        connected_limit = int(limit * prefer_connected)
        random_limit = limit - connected_limit
        
        neighbors = []
        
        # 1. 优先选择与已有节点有连接的邻居
        if connected_limit > 0:
            query = """
            UNWIND $node_ids AS n_id
            MATCH (n)-[r]-(m)
            WHERE elementId(n) = n_id AND NOT elementId(m) IN $existing_nodes
            WITH m, count(r) AS connection_strength, rand() AS r
            ORDER BY connection_strength DESC, r
            LIMIT $limit
            RETURN elementId(m) AS node_id, labels(m) AS labels, properties(m) AS properties
            """
            
            try:
                with self.graph_db.conn.session() as session:
                    result = session.run(
                        query, 
                        node_ids=node_ids,
                        existing_nodes=list(existing_nodes),
                        limit=connected_limit,
                    )
                    neighbors.extend([record.data() for record in result])
            except Exception as e:
                raise Exception(f"failed while get neighbour: {str(e)}")
        
        # 2. 补充随机节点，确保达到目标数量
        if random_limit > 0 and len(neighbors) < limit:
            remaining = limit - len(neighbors)
            query = """
            MATCH (m)
            WHERE NOT elementId(m) IN $existing_nodes
            WITH m, rand() AS r
            ORDER BY r
            LIMIT $limit
            RETURN elementId(m) AS node_id, labels(m) AS labels, properties(m) AS properties
            """
            
            try:
                with self.graph_db.conn.session() as session:
                    result = session.run(
                        query,
                        existing_nodes=list(existing_nodes) + [n['node_id'] for n in neighbors],
                        limit=remaining,
                    )
                    neighbors.extend([record.data() for record in result])
            except Exception  as e:
                print(f"failed while get neighbour: {str(e)}")
        
        return neighbors[:limit]  # 确保不超过限制数量
    
    def _get_relationships(self, node_ids: List[int]) -> List[Dict]:
        """获取节点集合之间的所有关系
        
        :param node_ids: 节点ID列表
        :return: 关系列表
        """
        if len(node_ids) < 2:
            return []
            
        query = """
        UNWIND $node_ids AS source_id
        MATCH (s)-[r]->(t)
        WHERE elementId(s) = source_id AND elementId(t) IN $node_ids
        RETURN elementId(r) AS rel_id, type(r) AS rel_type,
               elementId(s) AS start_node_id, elementId(t) AS end_node_id,
               properties(r) AS properties
        """
        
        try:
            with self.graph_db.conn.session() as session:
                result = session.run(query, node_ids=node_ids)
                return [record.data() for record in result]
        except Exception as e:
            raise Exception(f"failed while getting relationship: {str(e)}")
    
    def _get_random_subgraph(self, 
                       target_size: int, 
                       label: Optional[str] = None,
                       seed_proportion: float = 0.2,
                       expansion_steps: int = 2,
                       connectivity_bias: float = 0.7,
                       progress_interval: int = 10) -> Tuple[List[Dict], List[Dict]]:
        """
        抽样子图，尽可能保持连通性同时控制规模
        
        :param target_size: 目标子图节点数量
        :param label: 节点标签，None表示所有类型节点
        :param seed_proportion: 种子节点占目标规模的比例(0-1)
        :param expansion_steps: 邻居扩展步数，越大连通性可能越好
        :param connectivity_bias: 连接偏向系数(0-1)，越高越优先选择增强连通性的节点
        :param progress_interval: 进度日志输出间隔
        :return: (节点列表, 关系列表)
        """
        # 参数验证
        if target_size <= 0:
            raise ValueError("target size must be positive")
        if not (0 < seed_proportion < 1):
            raise ValueError("seed_proportion must between (0, 1)")
        if expansion_steps < 1:
            raise ValueError("expansion_steps must be at least 1")
        if not (0 <= connectivity_bias <= 1):
            raise ValueError("connectivity_bias must between [0, 1]")
        
        
        # 1. 检查总节点数是否足够
        total_nodes = self._count_total_nodes(label)
        if total_nodes < target_size:
            print(f"If the number of available nodes ({total_nodes}) is less than the target size ({target_size}), all nodes will be returned")
            target_size = total_nodes
        
        # 2. 计算种子节点数量
        seed_count = max(1, min(int(target_size * seed_proportion), target_size - 1))
        
        # 3. 选择种子节点
        seed_nodes = self._random_seed_nodes(label, seed_count)
        if not seed_nodes:
            raise Exception("failed while getting seed_nodes")
            
        # 存储所有选中的节点，用字典去重
        all_nodes = {node['node_id']: node for node in seed_nodes}
        current_ids = [node['node_id'] for node in seed_nodes]
        
        # 4. 多步扩展邻居节点
        remaining = target_size - len(all_nodes)
        step_size = max(1, remaining // expansion_steps)
        
        for step in range(expansion_steps):
            if remaining <= 0:
                break
                
            # 每步扩展的节点数量
            current_step_size = min(remaining, step_size)
            
            # 智能选择邻居
            new_neighbors = self._smart_neighbor_selection(
                node_ids=current_ids,
                existing_nodes=all_nodes.keys(),
                limit=current_step_size,
                prefer_connected=connectivity_bias
            )
            
            # 添加新节点
            for neighbor in new_neighbors:
                n_id = neighbor['node_id']
                if n_id not in all_nodes:
                    all_nodes[n_id] = neighbor
                    remaining -= 1
            
            # 更新当前节点列表（用于下一步扩展）
            current_ids = [n['node_id'] for n in new_neighbors]
            
        
        # 如果还没达到目标，补充随机节点
        if remaining > 0:
            suppls = self._smart_neighbor_selection(
                node_ids=list(all_nodes.keys()),
                existing_nodes=all_nodes.keys(),
                limit=remaining,
                prefer_connected=0.5  # 降低连接偏向，确保能快速补充节点
            )
            for node in suppls:
                n_id = node['node_id']
                if n_id not in all_nodes:
                    all_nodes[n_id] = node
                    remaining -= 1
        
        # 5. 获取所有选中节点之间的关系
        node_list = list(all_nodes.values())
        node_ids = [n['node_id'] for n in node_list]
        relationships = self._get_relationships(node_ids)
        
        
        return node_list, relationships
    
class RandomWalkSampler(SubGraphSampler):
    def __init__(self):
        self.sampled_nodes: Set[str] = set()
        self.sample_counter = 0
        # 用于控制DFS/BFS倾向的参数，每次采样随机调整以增加多样性
        self.dfs_bias_range = (0.3, 0.7)

    def get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> str:
        start_time = time.time()
        print("start sampling")
        nodes, relationships = self._get_random_subgraph(graph_db=graph_db, max_depth=max_depth, max_nodes=max_nodes, max_edges=max_edges)
        if nodes and relationships:
            subgraph_json = {
                "nodes": [{"id": node["node_id"], "labels": node["labels"], "properties": node["properties"]} for node in nodes],
                "relationships": [{"id": rel["rel_id"], "type": rel["rel_type"], "start_node_id": rel["start_node_id"], "end_node_id": rel["end_node_id"], "properties": rel["properties"]} for rel in relationships]
            }
            elapsed = time.time() - start_time
            print(f"Successfully retrieved subgraph with {len(nodes)} nodes and {len(relationships)} relationships. elapse: {elapsed: .2f}")
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

    def _random_walk_step(self, graph_db: GraphDb, current_nodes: Set[int], depth: int, 
                         max_depth: int, max_nodes: int, max_edges: int, 
                         dfs_bias: float) -> Tuple[Set[int], Set[int]]:
        """执行一步随机游走，返回新的节点和关系"""
        if not current_nodes or depth >= max_depth:
            return set(), set()
            
        # 构建当前节点参数
        params = {
            "current_nodes": list(current_nodes),
            "dfs_bias": dfs_bias,
            "max_possible": min(max_nodes - len(self.current_sample_nodes), max_edges - len(self.current_sample_edges))
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

    def _get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> Tuple[List[Dict], List[Dict]]:
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
        self.current_sample_edges = set()
        current_frontier = {start_node}
        dfs_bias = random.uniform(*self.dfs_bias_range)  # 随机DFS偏向，增加多样性
        
        # 执行多步随机游走
        for depth in range(max_depth):
            # 执行一步游走
            new_nodes, new_edges = self._random_walk_step(
                graph_db, current_frontier, depth, max_depth,
                max_nodes, max_edges, dfs_bias
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
                    
                    result = session.run(query, {
                        "node_ids": list(self.current_sample_nodes),
                        "edge_ids": list(self.current_sample_edges),
                        "remaining": remaining_edges
                    })
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
                    result = session.run(query, {
                        "edge_ids": list(self.current_sample_edges),
                        "node_ids": list(self.current_sample_nodes),
                        "remaining": remaining_nodes
                    })
                    supply_nodes = [record["node_id"] for record in result]
                    self.current_sample_nodes.update(supply_nodes)
                    # 同步记录已采样节点
                    self.sampled_nodes.update(supply_nodes)
        except Exception as e:
            raise Exception(f"[_get_random_subgraph] supply failed: {str(e)}")
        
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
                nodes_result = session.run(nodes_query, {"node_ids": list(self.current_sample_nodes)})
                nodes = [node for node in nodes_result]
                rels_result = session.run(rels_query, {"rel_ids": list(self.current_sample_edges)})
                rels = [rel for rel in rels_result]
        except Exception as e:
            raise Exception(f"[_get_random_subgraph] failed: {str(e)}")

        return nodes, rels