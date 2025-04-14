import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.artifact import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ContentType,
    SourceReference,
)
from app.core.service.artifact_service import ArtifactService
from app.core.service.file_service import FileService
from app.core.service.graph_db_service import GraphDbService
from app.core.service.service_factory import ServiceFactory
from app.core.toolkit.tool import Tool
from app.plugin.neo4j.resource.schema_operation import SchemaManager


class SchemaGetter(Tool):
    """Tool for getting the schema of a graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_schema.__name__,
            description=self.get_schema.__doc__ or "",
            function=self.get_schema,
        )

    async def get_schema(self, file_service: FileService) -> str:
        """Get the schema of the graph database.

        The graph schema defines the allowed structure and rules for the graph data in the database.
        """
        schema = await SchemaManager.read_schema(file_service=file_service)
        if len(schema) == 0:
            return "The schema is not defined yet. Please define the schema first."

        result = "# Neo4j Graph Schema\n\n"

        # vertices information
        result += "## Node Labels\n\n"
        for label, info in schema["nodes"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                else:
                    index_info = " (Indexed: not indexed)"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        # edges information
        result += "## Relationship Types\n\n"
        for label, info in schema["relationships"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += f"- Source Vertex Labels: {info['source_vertex_labels']}\n"
            result += f"- Target Vertex Labels: {info['target_vertex_labels']}\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        return result


class DataStatusCheck(Tool):
    """Tool for checking the current status of data in the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.check_data_status.__name__,
            description=self.check_data_status.__doc__ or "",
            function=self.check_data_status,
        )

    async def check_data_status(
        self,
        graph_db_service: GraphDbService,
        node_labels: Optional[List[str]] = None,
        relationship_labels: Optional[List[str]] = None,
        sample_limit: int = 3,
    ) -> str:
        """Check the current status of data in the graph database.

        This function provides an overview of the current state of the graph database,
        including counts of nodes by label, relationships by type, and optionally
        samples of node and relationship data.

        Args:
            node_labels (Optional[List[str]]): Specific node labels to check. If None, all labels will be checked.
            relationship_labels (Optional[List[str]]): Specific relationship types to check. If None, all types will be checked.
            sample_limit (int): Maximum number of sample records to return for each label/type. Default is 3.

        Returns:
            str: A formatted string containing database status information.
        """
        try:
            store = graph_db_service.get_default_graph_db()
            results: Dict[str, Any] = {}

            # keep track of whether the user provided specific labels/types
            user_provided_node_labels: bool = node_labels is not None
            user_provided_relationship_labels: bool = relationship_labels is not None
            # store the original lists if provided, for accurate reporting later
            original_node_labels = node_labels if user_provided_node_labels else []
            original_relationship_labels = (
                relationship_labels if user_provided_relationship_labels else []
            )

            with store.conn.session() as session:
                # 1. 获取总体统计信息
                total_stats = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->()
                    RETURN
                        count(DISTINCT n) as total_nodes,
                        count(DISTINCT r) as total_relationships
                """).single()

                results["总体统计"] = {
                    "总节点数": total_stats["total_nodes"] if total_stats else 0,
                    "总关系数": total_stats["total_relationships"] if total_stats else 0,
                }

                # 2. 获取所有节点标签列表（如果未指定）
                if node_labels is None:
                    labels_result = session.run(
                        "CALL db.labels() YIELD label RETURN collect(label) as labels"
                    ).single()
                    node_labels = labels_result["labels"] if labels_result else []

                # 3. 获取所有关系类型列表（如果未指定）
                if relationship_labels is None:
                    rel_types_result = session.run(
                        "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types"  # noqa: E501
                    ).single()
                    relationship_labels = rel_types_result["types"] if rel_types_result else []

                # 4. 获取节点标签统计和样例
                results["节点统计"] = {}
                results["节点样例"] = {}

                # Ensure node_labels is iterable even if fetching failed or DB is empty
                current_node_labels = node_labels if node_labels is not None else []
                for label in current_node_labels:
                    try:
                        # Escape label if it contains special characters (basic escaping)
                        safe_label = f"`{label.replace('`', '``')}`"
                        # 统计每个标签的节点数量
                        count_query = f"MATCH (n:{safe_label}) RETURN count(n) as count"
                        count_result = session.run(count_query).single()
                        node_count = count_result["count"] if count_result else 0
                        results["节点统计"][label] = node_count

                        # 获取每个标签的样例数据
                        if node_count > 0:
                            sample_query = f"MATCH (n:{safe_label}) RETURN n LIMIT {sample_limit}"
                            sample_results = list(session.run(sample_query))
                            samples = []

                            for record in sample_results:
                                node = record["n"]
                                node_props = dict(node)
                                samples.append(
                                    {
                                        "id": node_props.get(
                                            "id", node.element_id
                                        ),  # Use element_id as fallback
                                        "properties": node_props,
                                    }
                                )
                            results["节点样例"][label] = samples
                    except Exception as label_e:
                        print(f"Warning: Failed to process node label '{label}': {label_e}")
                        results["节点统计"][label] = f"Error: {label_e}"

                # 5. 获取关系类型统计和样例
                results["关系统计"] = {}
                results["关系样例"] = {}

                # Ensure relationship_labels is iterable
                current_relationship_labels = (
                    relationship_labels if relationship_labels is not None else []
                )
                for rel_type in current_relationship_labels:
                    try:
                        # Escape relationship type if it contains special characters (basic escaping)
                        safe_rel_type = f"`{rel_type.replace('`', '``')}`"
                        # 统计每个类型的关系数量
                        count_query = f"MATCH ()-[r:{safe_rel_type}]->() RETURN count(r) as count"
                        count_result = session.run(count_query).single()
                        rel_count = count_result["count"] if count_result else 0
                        results["关系统计"][rel_type] = rel_count

                        # 获取每个类型的样例数据
                        if rel_count > 0:
                            # Enhanced sample query to handle missing labels/ids gracefully
                            sample_query = f"""
                                MATCH (a)-[r:{safe_rel_type}]->(b)
                                RETURN
                                    elementId(r) as rel_element_id,
                                    type(r) as type,
                                    properties(r) as props,
                                    coalesce(labels(a)[0], 'Unknown') as source_label,
                                    coalesce(a.id, elementId(a)) as source_id,
                                    coalesce(labels(b)[0], 'Unknown') as target_label,
                                    coalesce(b.id, elementId(b)) as target_id
                                LIMIT {sample_limit}
                            """
                            sample_results = list(session.run(sample_query))
                            samples = []

                            for record in sample_results:
                                samples.append(
                                    {
                                        "type": record["type"],
                                        "properties": record["props"],
                                        "source": f"{record['source_label']}(id: {record['source_id']})",
                                        "target": f"{record['target_label']}(id: {record['target_id']})",
                                        "element_id": record[
                                            "rel_element_id"
                                        ],  # Include relationship element ID
                                    }
                                )

                            results["关系样例"][rel_type] = samples
                    except Exception as rel_e:
                        print(f"Warning: Failed to process relationship type '{rel_type}': {rel_e}")
                        results["关系统计"][rel_type] = f"Error: {rel_e}"

            # 格式化输出结果
            output = []

            # 总体统计
            output.append("# 图数据库当前状态")
            output.append("\n## 总体统计")
            output.append(f"- 总节点数: {results['总体统计']['总节点数']}")
            output.append(f"- 总关系数: {results['总体统计']['总关系数']}")

            # 节点统计
            output.append("\n## 节点统计")
            # Check if any counts > 0 or if specific labels were requested but none found
            node_counts_found = any(
                v > 0 for v in results["节点统计"].values() if isinstance(v, int)
            )

            if not node_counts_found:
                # --- Start Modification ---
                if user_provided_node_labels:
                    # User specified labels, but none were found (or had count 0)
                    output.append(f"- 数据库中未找到与指定标签 {original_node_labels} 相关的节点")
                elif not current_node_labels and results["总体统计"]["总节点数"] == 0:
                    # No labels specified, and no labels exist in the DB (implies no nodes)
                    output.append("- 数据库中当前无任何节点标签或节点")
                else:
                    # No labels specified, labels *might* exist, but all counts are 0
                    output.append("- 数据库中所有已检查的节点标签下均无节点")
            # --- End Modification ---
            else:
                for label, count in results["节点统计"].items():
                    if isinstance(count, int):
                        output.append(f"- {label}: {count} 个")
                    else:  # Handle potential error messages stored during processing
                        output.append(f"- {label}: {count}")

            # 关系统计
            output.append("\n## 关系统计")
            rel_counts_found = any(
                v > 0 for v in results["关系统计"].values() if isinstance(v, int)
            )

            if not rel_counts_found:
                # --- Start Modification ---
                if user_provided_relationship_labels:
                    # User specified types, but none were found (or had count 0)
                    output.append(
                        f"- 数据库中未找到与指定类型 {original_relationship_labels} 相关的关系"
                    )
                elif not current_relationship_labels and results["总体统计"]["总关系数"] == 0:
                    # No types specified, and no types exist in the DB (implies no relationships)
                    output.append("- 数据库中当前无任何关系类型或关系")
                else:
                    # No types specified, types *might* exist, but all counts are 0
                    output.append("- 数据库中所有已检查的关系类型下均无关系")
                # --- End Modification ---
            else:
                for rel_type, count in results["关系统计"].items():
                    if isinstance(count, int):
                        output.append(f"- {rel_type}: {count} 个")
                    else:  # Handle potential error messages
                        output.append(f"- {rel_type}: {count}")

            # 节点样例
            if any(results["节点样例"].values()):
                output.append("\n## 节点样例")
                for label, samples in results["节点样例"].items():
                    if samples:
                        output.append(f"\n### {label} 节点样例 (最多打印 {sample_limit} 个)")
                        for i, sample in enumerate(samples, 1):
                            output.append(f"样例 {i}:")
                            # Use element_id if specific 'id' property is missing
                            output.append(f"- ID: {sample['id']}")
                            output.append("- 属性:")
                            if sample["properties"]:
                                for prop_key, prop_value in sample["properties"].items():
                                    output.append(f"  - {prop_key}: {prop_value}")
                            else:
                                output.append("  - (无属性)")

            # 关系样例
            if any(results["关系样例"].values()):
                output.append("\n## 关系样例")
                for rel_type, samples in results["关系样例"].items():
                    if samples:
                        output.append(f"\n### {rel_type} 关系样例 (最多打印 {sample_limit} 个)")
                        for i, sample in enumerate(samples, 1):
                            output.append(f"样例 {i}:")
                            output.append(
                                f"- Element ID: {sample['element_id']}"
                            )  # Added element ID
                            output.append(f"- 源节点: {sample['source']}")
                            output.append(f"- 目标节点: {sample['target']}")
                            if sample["properties"]:
                                output.append("- 关系属性:")
                                for prop_key, prop_value in sample["properties"].items():
                                    output.append(f"  - {prop_key}: {prop_value}")
                            else:
                                output.append("- (无关系属性)")

            return "\n".join(output)

        except Exception as e:
            # Log the exception traceback for debugging
            import traceback

            traceback.print_exc()
            raise Exception(f"检查数据状态失败: {str(e)}") from e


class DataImport(Tool):
    """Tool for importing data into a graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.import_triplet_data.__name__,
            description=self.import_triplet_data.__doc__ or "",
            function=self.import_triplet_data,
        )

    async def import_triplet_data(
        self,
        graph_db_service: GraphDbService,
        artifact_service: ArtifactService,
        session_id: str,
        job_id: str,
        source_label: str,
        source_primary_key: str,
        source_properties: Dict[str, Any],
        target_label: str,
        target_primary_key: str,
        target_properties: Dict[str, Any],
        relationship_label: str,
        relationship_properties: Dict[str, Any],
    ) -> str:
        """Import the graph data into the database by processing the triplet.
        Each relationship and its associated source/target nodes are processed as a triple unit.
        This function can be called multiple times to import multiple triplets.
        Please parse the arguments correctly after reading the schema, so that the data base accepts
            the data.

        Data Validation Rules:
            - All entities must have a valid primary key defined in their properties
            - Entity and relationship labels must exist in the database schema, and the constraints of the edges
                present the direction of the relationship. For example, constraints [A, B] and [B, A] are different
                directions of the relationship. Never flip the direction of the relationship
            - Properties must be a dictionary and contain all required fields defined in schema
            - Invalid entities or relationships will be silently skipped
            - Date values must be in YYYY-MM-DD format, for example, "2022-01-01" or
                "2022-01-01T00:00:00Z", but "208-01-01" (without a 0 in 208) is invalid
            - Use the English letters (by snake_case naming) for the field if it is related to the identity
                instead of the number (e.g., "LiuBei" for person_id, instead of "123")

        Args:
            session_id (str): The session ID
            job_id (str): The job ID
            source_label (str): Label of the source node (e.g., "Person"), defined in the graph schema
            source_primary_key (str): Primary key of the source node (e.g., "id"), defined in the graph schema
            source_properties (Dict[str, Any]): Properties of the source node. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema
            target_label (str): Label of the target node (e.g., "Event"), defined in the graph schema
            target_primary_key (str): Primary key of the target node (e.g., "id"), defined in the graph schema
            target_properties (Dict[str, Any]): Properties of the target node. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema
            relationship_label (str): Label of the relationship, defined in the graph schema
            relationship_properties (Dict[str, Any]): Properties of the relationship. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema

        Returns:
            str: Summary of the import operation, including counts of entities and relationships
                processed, created, and updated.
        """  # noqa: E501

        def format_date(value: str) -> str:
            """Format date value to ensure it has a leading zero in the year."""
            date_pattern = r"^(\d{3})-(\d{2})-(\d{2})(T[\d:]+Z)?$"
            match = re.match(date_pattern, value)
            if match:
                year = match.group(1)
                if len(year) == 3:
                    time_part = match.group(4) or ""
                    return f"0{year}-{match.group(2)}-{match.group(3)}{time_part}"
            return value

        def format_property_value(value: Any) -> str:
            """Format property value for Cypher query."""
            if value is None:
                return "null"
            elif isinstance(value, int | float):
                return str(value)
            else:
                str_value = str(value)
                str_value = str_value.replace("'", "\\'")
                return f"'{str_value}'"

        def format_properties(properties: Dict[str, Any]) -> str:
            """Format properties dictionary to Cypher property string."""
            props = []
            for key, value in properties.items():
                if key in ["date", "start_date", "end_date", "start_time"] and isinstance(
                    value, str
                ):
                    value = format_date(value)
                props.append(f"{key}: {format_property_value(value)}")
            return "{" + ", ".join(props) + "}"

        try:
            # 格式化属性
            source_props = format_properties(source_properties)
            target_props = format_properties(target_properties)
            rel_props = format_properties(relationship_properties)

            # 构建Cypher语句
            cypher = f"""
            MERGE (source:{source_label} {{{source_primary_key}: {format_property_value(source_properties[source_primary_key])}}})
            ON CREATE SET source = {source_props}
            ON MATCH SET source = {source_props}
            WITH source
            MERGE (target:{target_label} {{{target_primary_key}: {format_property_value(target_properties[target_primary_key])}}})
            ON CREATE SET target = {target_props}
            ON MATCH SET target = {target_props}
            WITH source, target
            MERGE (source)-[r:{relationship_label}]->(target)
            ON CREATE SET r = {rel_props}
            ON MATCH SET r = {rel_props}
            RETURN source, target, r
            """  # noqa: E501

            store = graph_db_service.get_default_graph_db()
            with store.conn.session() as session:
                # 执行导入操作
                print(f"Executing statement: {cypher}")
                result = session.run(cypher)
                summary = result.consume()
                nodes_created = summary.counters.nodes_created
                nodes_updated = summary.counters.properties_set
                rels_created = summary.counters.relationships_created

                # 获取本次操作的详细信息
                details = {
                    "source": f"{source_label}(id: {source_properties[source_primary_key]})",
                    "target": f"{target_label}(id: {target_properties[target_primary_key]})",
                    "relationship": f"{relationship_label}",
                }

                # 获取数据库当前状态
                # 1. 节点统计
                node_counts = {}
                for label in [source_label, target_label]:
                    result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    node_counts[label] = result.single()["count"]

                # 2. 关系统计
                rel_count = session.run(
                    f"MATCH ()-[r:{relationship_label}]->() RETURN count(r) as count"
                ).single()["count"]

                # 3. 总体统计
                total_stats = session.run("""
                    MATCH (n) 
                    OPTIONAL MATCH (n)-[r]->() 
                    RETURN 
                        count(DISTINCT n) as total_nodes,
                        count(DISTINCT r) as total_relationships
                """).single()

            with store.conn.session() as session:
                # 获取所有节点和边
                all_nodes = session.run("MATCH (n) RETURN n")
                all_edges = session.run("MATCH ()-[r]->() RETURN r")

                # 构造 GraphMessage JSON
                vertices = [
                    {
                        "id": node.element_id if hasattr(node, "element_id") else node.id,
                        "label": list(node.labels)[0]
                        if hasattr(node, "labels") and node.labels
                        else "",
                        "properties": dict(node.items()),
                    }
                    for record in all_nodes
                    for node in [record.get("n")]
                ]

                edges = [
                    {
                        "source": relationship.start_node.element_id
                        if hasattr(relationship.start_node, "element_id")
                        else relationship.start_node.id,
                        "target": relationship.end_node.element_id
                        if hasattr(relationship.end_node, "element_id")
                        else relationship.end_node.id,
                        "label": relationship.type,
                        "properties": dict(relationship.items()),
                    }
                    for record in all_edges
                    for relationship in [record.get("r")]
                ]

                data_graph_dict = {"vertices": vertices, "edges": edges}

                # 保存 graph type artifact
                artifacts: List[Artifact] = artifact_service.get_artifacts_by_job_id_and_type(
                    job_id=job_id, content_type=ContentType.GRAPH
                )

                if len(artifacts) == 0:
                    artifact = Artifact(
                        content_type=ContentType.GRAPH,
                        content=data_graph_dict,
                        source_reference=SourceReference(job_id=job_id, session_id=session_id),
                        status=ArtifactStatus.FINISHED,
                        metadata=ArtifactMetadata(version=1, description="It is the data graph."),
                    )
                    artifact_service.save_artifact(artifact=artifact)
                else:
                    artifact_service.increment_and_save(
                        artifact=artifacts[0], new_content=data_graph_dict
                    )

                return f"""数据导入成功！
本次操作详情：
- 创建/更新的节点：
- 源节点: {details["source"]}
- 目标节点: {details["target"]}
- 创建的关系: {details["relationship"]}
- 操作统计：
- 新建节点数: {nodes_created}
- 更新属性数: {nodes_updated}
- 新建关系数: {rels_created}

当前数据库状态：
- 节点统计：
- {source_label}: {node_counts[source_label]} 个
- {target_label}: {node_counts[target_label]} 个
- 关系统计：
- {relationship_label}: {rel_count} 个
- 总体统计：
- 总节点数: {total_stats["total_nodes"]}
- 总关系数: {total_stats["total_relationships"]}
"""

        except Exception as e:
            raise Exception(f"Failed to import data: {str(e)}") from e


SCHEMA_BOOK = """
# Neo4j Schema 指南 (LLM 友好版)

本指南帮助理解Neo4j的数据模型和Schema设计。

## 1. 节点 (Node) 定义

Neo4j中的节点代表实体，具有以下特征：

### 1.1 标签 (Labels)
- 节点可以有一个或多个标签
- 标签用于分类和区分不同类型的节点
- 示例：`:Person`、`:Location`

### 1.2 属性 (Properties)
- 属性是键值对
- 支持的数据类型：
  - String：字符串
  - Integer：整数
  - Float：浮点数
  - Boolean：布尔值
  - Point：空间点
  - Date/DateTime：日期时间
  - Duration：时间段
- 属性可以建立索引提高查询性能

### 1.3 约束 (Constraints)
- 唯一性约束：确保属性值唯一性
- 示例：`CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE`

## 2. 关系 (Relationship) 定义

关系连接节点，具有以下特征：

### 2.1 类型 (Types)
- 关系必须有一个类型
- 关系类型通常使用大写字母
- 示例：`:KNOWS`、`:WORKS_FOR`

### 2.2 属性
- 关系也可以有属性
- 属性数据类型与节点相同
- 可以为关系属性创建索引

### 2.3 方向性
- 关系有方向，但可以双向查询
- 格式：`(source)-[relationship]->(target)`

## 3. 索引 (Indexes)
- 支持节点和关系的属性索引
- 用于优化查询性能
- 示例：`CREATE INDEX person_name_idx IF NOT EXISTS FOR (n:Person) ON (n.name)`

## 4. 最佳实践
- 使用有意义的标签名
- 合理使用索引提升性能
- 根据查询模式设计数据模型
"""


DaoFactory.initialize(DbSession())
ServiceFactory.initialize()


async def main():
    your_instance = DataStatusCheck()
    graph_db_service = GraphDbService()  # Your actual service instance

    print("--- Checking status with no specific labels/types (empty DB simulation) ---")
    status_all_empty = await your_instance.check_data_status(graph_db_service)
    print(status_all_empty)

    print("\n--- Checking status for specific labels/types (empty DB simulation) ---")
    status_specific_empty = await your_instance.check_data_status(
        graph_db_service, node_labels=["character"], relationship_labels=["BELONGS_TO"]
    )
    print(status_specific_empty)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
