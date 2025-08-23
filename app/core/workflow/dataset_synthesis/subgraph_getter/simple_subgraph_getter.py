from app.core.toolkit.graph_db.graph_db import GraphDb
from app.core.workflow.dataset_synthesis.data_synthesis import SubGraphGetter
import json

class SimpleRandomSubGraphGetter(SubGraphGetter):
    def get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> str:
        # 随机选择一个起始节点
        try:
            start_node = self._get_random_node(graph_db=graph_db)
            if not start_node:
                # TODO: use logger warning
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

        # 将子图转换为 JSON 格式
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