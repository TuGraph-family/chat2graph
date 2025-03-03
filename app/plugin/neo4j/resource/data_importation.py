import re
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.toolkit.tool import Tool
from app.plugin.neo4j.neo4j_store import get_neo4j
from app.plugin.neo4j.resource.read_doc import SchemaManager

DOC_CONTENT = """
# 罗密欧与朱丽叶：故事梗概与人物关系

## 背景

故事发生在意大利维罗纳城。维罗纳城中有两个世代为敌的家族：蒙太古家族和凯普莱特家族。两个家族之间的仇恨由来已久，其成员经常在城中发生冲突。

## 主要人物及关系

1. **罗密欧**：蒙太古家族的儿子，年轻的贵族。
2. **朱丽叶**：凯普莱特家族的女儿，14岁。
3. **蒙太古先生**：罗密欧的父亲，蒙太古家族的家主。
4. **蒙太古夫人**：罗密欧的母亲。
5. **凯普莱特先生**：朱丽叶的父亲，凯普莱特家族的家主。
6. **凯普莱特夫人**：朱丽叶的母亲。
7. **茂丘西奥**：罗密欧的好友，维罗纳王子的亲戚。
8. **班伏里奥**：罗密欧的表兄，也是蒙太古家族成员。
9. **提拜尔特**：朱丽叶的表兄，凯普莱特家族成员。
10. **朱丽叶的奶妈**：朱丽叶的照料者和保密者。
11. **神父劳伦斯**：维罗纳的方济各会神父，同时是罗密欧的精神顾问。
12. **巴黎伯爵**：贵族，想要娶朱丽叶的求婚者。
13. **巴尔萨扎**：罗密欧的忠实仆人。
14. **埃斯卡勒斯王子**：维罗纳的统治者，对两家的争斗感到厌烦。

## 故事情节

### 第一部分：初次相遇

1. 维罗纳城内，蒙太古和凯普莱特两家的仆人在街头发生争斗。埃斯卡勒斯王子出面制止，并宣布如再次发生冲突，参与者将被处死。

2. 罗密欧当时正为一位叫罗瑟琳的女子的拒绝而伤心。

3. 班伏里奥建议罗密欧去参加凯普莱特家举办的舞会，以忘记罗瑟琳。

4. 同一时间，凯普莱特夫人告诉朱丽叶，巴黎伯爵想要娶她，并且凯普莱特先生已经同意。朱丽叶表示她从未想过婚姻。

5. 罗密欧、班伏里奥和茂丘西奥戴着面具潜入凯普莱特家的舞会。在舞会上，罗密欧一眼看见朱丽叶就爱上了她。

6. 罗密欧与朱丽叶交谈并跳舞。后来罗密欧才知道朱丽叶是凯普莱特家的女儿，朱丽叶也得知罗密欧是蒙太古家的儿子。

7. 舞会结束后，罗密欧不愿离去，偷偷溜到凯普莱特家的花园里。他听到朱丽叶在阳台上自言自语，表达对他的感情，并为他是蒙太古家的人而苦恼。

8. 罗密欧现身，两人互诉爱意，约定第二天秘密结婚。

### 第二部分：秘密婚礼与冲突升级

1. 次日，罗密欧去找神父劳伦斯，请求他为他和朱丽叶主持婚礼。神父劳伦斯同意，希望通过这段婚姻结束两家的仇恨。

2. 朱丽叶借口去教堂忏悔，与罗密欧在神父劳伦斯的见证下秘密结婚。

3. 婚礼后，罗密欧在街头遇到提拜尔特。提拜尔特因罗密欧闯入舞会而愤怒，挑衅罗密欧。罗密欧因刚与朱丽叶结婚，拒绝与提拜尔特决斗。

4. 茂丘西奥误以为罗密欧是懦弱，替罗密欧应战。在打斗中，罗密欧试图阻止两人，却导致茂丘西奥被提拜尔特刺伤致死。

5. 罗密欧因好友之死愤怒，杀死了提拜尔特，随后逃离现场。

6. 埃斯卡勒斯王子听取事件经过后，判处罗密欧终身流放，如再踏入维罗纳一步就处死。

### 第三部分：分离与计划

1. 朱丽叶得知表兄提拜尔特被罗密欧杀死的消息，陷入两难境地：既为表兄之死悲痛，又担心丈夫的命运。

2. 神父劳伦斯安排罗密欧在离开维罗纳前与朱丽叶见最后一面。两人在朱丽叶的房间度过最后一晚，黎明前罗密欧离开，前往曼图亚。

3. 凯普莱特先生为使朱丽叶走出悲伤，决定加速她与巴黎伯爵的婚事，定在三天后举行。

4. 朱丽叶拒绝这门婚事，凯普莱特先生勃然大怒，威胁要与女儿断绝关系。

5. 绝望的朱丽叶去找神父劳伦斯寻求帮助。神父给了她一种药水，饮用后会让她看似死亡，实则只是深度睡眠，持续42小时。

6. 神父的计划是：朱丽叶假死后会被安放在家族墓穴，神父会通知罗密欧这个计划，让他在朱丽叶醒来时前来接她，两人一起逃往曼图亚。

7. 朱丽叶回家后，假装同意与巴黎伯爵的婚事，实则在婚礼前夜喝下了药水，陷入假死状态。

### 第四部分：误会与悲剧

1. 朱丽叶被发现"死"在床上，原定的婚礼变成了葬礼。她被安放在凯普莱特家的墓穴中。

2. 神父劳伦斯派一位修士前往曼图亚告知罗密欧计划，但因城中爆发瘟疫，修士被隔离，未能及时送达信件。

3. 罗密欧的仆人巴尔萨扎得知朱丽叶"死亡"的消息，立即赶到曼图亚告诉罗密欧。

4. 罗密欧以为朱丽叶真的死了，买了一瓶毒药，决定回到维罗纳与朱丽叶同死。

5. 罗密欧回到维罗纳，在墓穴外遇到前来悼念朱丽叶的巴黎伯爵。两人决斗，罗密欧杀死了巴黎伯爵。

6. 罗密欧进入墓穴，看到"死去"的朱丽叶，喝下毒药自杀。

7. 朱丽叶醒来，发现罗密欧已死，悲痛欲绝。神父劳伦斯赶到墓穴，试图带走朱丽叶，但她拒绝离开。

8. 神父听到巡逻队的脚步声不得不离开。朱丽叶拿起罗密欧的匕首，刺入自己的胸膛，死在罗密欧身边。

### 第五部分：和解

1. 巡逻队发现了罗密欧、朱丽叶和巴黎伯爵三具尸体。蒙太古家和凯普莱特家的人都赶到墓穴。

2. 神父劳伦斯讲述了事情的经过，两家族长意识到他们多年的仇恨导致了这场悲剧。

3. 蒙太古先生和凯普莱特先生决定结束两家的仇恨，在维罗纳广场上为罗密欧和朱丽叶建立一座金像，作为和解的象征。

4. 自此，两家的仇恨结束，维罗纳城恢复和平。

## 关键关系概述

1. **家族关系**：
   - 罗密欧是蒙太古家族的儿子
   - 朱丽叶是凯普莱特家族的女儿
   - 蒙太古家族和凯普莱特家族是世仇

2. **爱情关系**：
   - 罗密欧爱上朱丽叶
   - 朱丽叶爱上罗密欧
   - 巴黎伯爵求娶朱丽叶

3. **友谊关系**：
   - 班伏里奥是罗密欧的表兄和朋友
   - 茂丘西奥是罗密欧的好友
   - 提拜尔特是朱丽叶的表兄

4. **辅助关系**：
   - 神父劳伦斯帮助罗密欧和朱丽叶
   - 朱丽叶的奶妈是朱丽叶的支持者
   - 巴尔萨扎是罗密欧的忠实仆人

5. **权力关系**：
   - 埃斯卡勒斯王子是维罗纳的统治者
   - 凯普莱特先生对朱丽叶有决定权
   - 蒙太古先生是罗密欧的父亲

## 主要事件顺序

1. 两家族仆人街头斗殴
2. 罗密欧参加凯普莱特家舞会
3. 罗密欧与朱丽叶相爱
4. 罗密欧与朱丽叶秘密结婚
5. 罗密欧杀死提拜尔特
6. 罗密欧被流放
7. 朱丽叶被迫答应嫁给巴黎伯爵
8. 朱丽叶服药假死
9. 罗密欧误信朱丽叶死讯
10. 罗密欧自杀
11. 朱丽叶自杀
12. 两家族和解

## 原因与结果链

1. 因为两家族的仇恨，所以罗密欧和朱丽叶的爱情被阻碍
2. 因为罗密欧参加舞会，所以他遇见并爱上朱丽叶
3. 因为提拜尔特杀死茂丘西奥，所以罗密欧杀死提拜尔特
4. 因为罗密欧杀死提拜尔特，所以他被流放
5. 因为罗密欧被流放，所以朱丽叶被迫嫁给巴黎伯爵
6. 因为朱丽叶不想嫁给巴黎伯爵，所以她服药假死
7. 因为信件未送达，所以罗密欧误以为朱丽叶真死了
8. 因为罗密欧以为朱丽叶死了，所以他自杀
9. 因为罗密欧自杀，所以朱丽叶也自杀
10. 因为罗密欧和朱丽叶的死，所以两家族最终和解
"""


class DocumentReader(Tool):
    """Tool for analyzing document content."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.read_document.__name__,
            description=self.read_document.__doc__ or "",
            function=self.read_document,
        )

    async def read_document(self, doc_name: str, chapter_name: str) -> str:
        """Read the document content given the document name and chapter name.

        Args:
            doc_name (str): The name of the document.
            chapter_name (str): The name of the chapter of the document.

        Returns:
            The content of the document.
        """

        return DOC_CONTENT


class SchemaGetter(Tool):
    """Tool for getting the schema of a graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_schema.__name__,
            description=self.get_schema.__doc__ or "",
            function=self.get_schema,
        )

    async def get_schema(self) -> str:
        """获取图数据库的 schema 信息"""
        schema = await SchemaManager.read_schema()

        result = "# Neo4j Graph Schema\n\n"

        # 节点信息
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

        # 关系信息
        result += "## Relationship Types\n\n"
        for label, info in schema["relationships"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        return result


class DataImport(Tool):
    """Tool for importing data into a graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.import_data.__name__,
            description=self.import_data.__doc__ or "",
            function=self.import_data,
        )

    async def import_data(
        self,
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
            source_label (str): Label of the source node (e.g., "Person"), defined in the graph schema
            source_primary_key (str): Primary key of the source node (e.g., "id")
            source_properties (Dict[str, Any]): Properties of the source node. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema
            target_label (str): Label of the target node, defined in the graph schema
            target_primary_key (str): Primary key of the target node
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
            """

            store = get_neo4j()
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
            raise Exception(f"Failed to import data: {str(e)}")


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
