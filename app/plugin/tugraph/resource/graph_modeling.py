import json
from typing import Dict, List, Optional, Set, Union

from app.core.common.system_env import SystemEnv
from app.core.model.message import ModelMessage
from app.core.model.task import ToolCallContext
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool

CYPHER_GRAMMER = """
===== TuGraph Cypher 语法书 =====

createVertexLabelByJson 命令用于创建顶点标签，基本语法：

```
CALL db.createVertexLabelByJson('{
    "label": "标签名",
    "primary": "主键字段名",
    "type": "VERTEX",
    "properties": [
        {
            "name": "字段名",
            "type": "字段类型",
            "optional": True/False,
            "index": True/False,
        }
        // ... 更多属性
    ]
}');
```

createEdgeLabelByJson 命令用于创建边标签，基本语法：

```
CALL db.createEdgeLabelByJson('{
    "label": "边标签名",
    "type": "EDGE",
    "properties": [
        {
            "name": "type",
            "type": "STRING",
            "optional": False,
        },
        // ... 更多属性
    ],
    "constraints": [
        ["源实体标签名", "目标实体标签名"],
    ]
}');
```

关键参数说明：

1. 顶点标签必填字段：
   - label: 节点标签名
   - primary: 主键字段名
   - type: 必须为 "VERTEX"
   - properties: 至少包含主键属性

2. 边标签必填字段：
   - label: 边标签名
   - type: 必须为 "EDGE"
   - properties: 至少包含主键属性

属性定义规则：
- name: 属性名
- type: 属性类型（见下方支持的数据类型）
- optional: 是否可选（True/False）
- index: 是否建立索引（可选参数）(字符串字段如果需要查询，建议设置 index: True)

支持的数据类型：
- 整数类型：INT8, INT16, INT32, INT64
- 浮点类型：FLOAT, DOUBLE
- 其他类型：STRING, BOOL, DATE, DATETIME

重要注意事项：

1. 格式要求：
   - JSON 必须用单引号包裹
   - 所有字符串值使用双引号
   - 标签名和字段名不能包含特殊字符

2. 字段规则：
   - 主键字段必须设置 optional: False

=====
"""

# operation 1: Document Analysis
DOC_ANALYSIS_PROFILE = """
你是一位专业的文档分析专家，专注于从文档中提取关键信息，为知识图谱的构建奠定坚实基础。
你需要理解文档内容。请注意，你分析的文档可能只是全集的一个子集，需要通过局部推断全局。
请注意，你的任务不是需要操作图数据库。你的任务是分析文档，为后续的 knowledge graph modeling 提供重要信息。
"""  # noqa: E501

DOC_ANALYSIS_INSTRUCTION = """
请仔细阅读给定的文档，并按以下要求完成任务：

1. 语义层分析
   - 显式信息（比如，关键词、主题、术语定义）
   - 隐式信息（比如，深层语义、上下文关联、领域映射）

2. 关系层分析  
   - 实体关系（比如，直接关系、间接关系、层次关系）。时序关系（比如，状态变迁、演化规律、因果链条）

3. 知识推理
   - 模式推理、知识补全

请确保你的分析全面、细致，并为每一个结论提供充分的理由。
"""

DOC_ANALYSIS_OUTPUT_SCHEMA = """
{
    "domain": "文档所属领域的详细描述，解释该领域的主要业务和数据特点",
    "data_full_view": "对文档数据全貌的详细推测，包括数据结构、规模、实体关系等，并提供思考链路和理由",
    "concepts": [
        {"concept": "概念名称", "description": "概念的详细描述", "importance": "概念在文档中的重要性"},
        ...
    ],
    "properties": [
        {"concept": "所属概念", "property": "属性名称", "description": "属性的详细描述", "data_type": "属性的数据类型"},
        ...
    ],
    "potential_relations": [
        {"relation": "关系类型", "entities_involved": ["实体1", "实体2", ...], "description": "关系的详细描述", "strength": "关系的强度或重要性"},
        ...
    ],
    "document_insights": "其他重要（多条）信息或（多个）发现，它们独属于本文档的特殊内容，请用分号隔开。",
    "document_snippets": "文档中的关键片段，用于支撑你的分析结论，提供上下文信息。",
}
"""  # noqa: E501

# operation 2: Concept Modeling
CONCEPT_MODELING_PROFILE = """
你是一位知识图谱建模专家，擅长将概念和关系转化为图数据库模式。你需要设计合适的实体-关系模型，然后操作图数据库，确保任务的顺利完成。
"""

CONCEPT_MODELING_INSTRUCTION = """
你应该基于文档分析的结果，完成概念建模的任务，同时确保图建模的正确性和可达性。

1. 实体类型定义
- 从以下维度思考和定义实体类型：
  * 时间维度：事件、时期、朝代等时序性实体
  * 空间维度：地点、区域、地理特征等空间性实体
  * 社会维度：人物、组织、势力等社会性实体（可选）
  * 文化维度：思想、文化、典故等抽象实体（可选）
  * 物理维度：物品、资源、建筑等具象实体（可选）
- 建立实体类型的层次体系：
  * 定义上下位关系（如：人物-君主-诸侯）
  * 确定平行关系（如：军事人物、政治人物、谋士）
  * 设计多重继承关系（如：既是军事人物又是谋士）
- 为每个实体类型设计丰富的属性集：
  * 基础属性：标识符、名称、描述等
  * 类型特有属性：根据实体类型特点定义
  * 关联属性：引用其他实体的属性
- 考虑实体的时态性：
  * 属性的时效性（如：官职随时间变化）（可选）
  * 状态的可变性（如：阵营的转变）（可选）
- 为每个实体类型定义完整的属性集，包括必需属性和可选属性
- 确保实体类型之间存在潜在的关联路径，但保持概念边界的独立性

2. 关系类型设计
- 定义实体间的关系类型，包括直接关系、派生关系和潜在关系
- 明确关系的方向性（有向）、设计关系的属性集
- 通过关系组合，验证关键实体间的可达性
- （可选）考虑添加反向关系以增强图的表达能力

3. Schema生成
- 使用 graph schema creator 的函数，可以使用该函数生成 schema，为 vertex 和 edge 创建特殊的 schema。你不能直接写 cypher 语句，而是使用工具函数来帮助你操作数据库。
- 请注意：Schema 不是在 DB 中插入节点、关系等具体的数据，而是定义图数据库的模式（schema/label）。预期应该是定义是实体的类型、关系的类型、约束等这些东西。
- 任务的背景是知识图谱，所以，不要具体的某个实体，而是相对通用的实体。比如，可以从时间、抽象概念、物理实体和社会实体等多个主要维度来考虑。
- 需要多次读取 TuGraph 现有的 Schema，目的是确保根据 DDL 创建的 schema 符合预期。

4. 验证图的可达性
- 可达性是图数据库的核心特性之一，确保图中的实体和关系之间存在有效的连接路径，以支持复杂的查询需求。这在图建模中很重要，因为如果图不可达，将无法在构建一个完整的知识图谱。
- 通过查询图数据库，获取图的结构信息，验证实体和关系的可达性。
"""  # noqa: E501

CONCEPT_MODELING_OUTPUT_SCHEMA = """
{
    "reachability": "说明实体和关系之间的可达性，是否存在有效的连接路径",
    "stauts": "模型状态，是否通过验证等",
    "entity_label": "成功创建的实体标签",
    "relation_label": "成功创建的关系标签",
}
"""

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
"""  # noqa: E501


class DocumentReader(Tool):
    """Tool for analyzing document content."""

    def __init__(self):
        super().__init__(
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


class VertexLabelAdder(Tool):
    """Tool for generating Cypher statements to create vertex labels in TuGraph."""

    def __init__(self):
        super().__init__(
            name=self.create_vertex_label_by_json_schema.__name__,
            description=self.create_vertex_label_by_json_schema.__doc__ or "",
            function=self.create_vertex_label_by_json_schema,
        )

    async def create_vertex_label_by_json_schema(
        self,
        graph_db_service: GraphDbService,
        label: str,
        primary: str,
        properties: List[Dict[str, Union[str, bool]]],
    ) -> str:
        """Generate a TuGraph vertex label statement, and then operator the TuGraph database to
        create the labels in the database.
        Field names can only contain letters, numbers, and underscores.

        Args:
            label (str): The name of the vertex label to create
            primary (str): The name of the primary key field
            properties (List[Dict]): List of property definitions, each containing:
                - name (str): Property name
                - type (str): Property type (e.g., 'STRING', 'INT32', 'DOUBLE', 'BOOL', 'DATE',
                    'DATETIME', do not support 'LIST' and 'MAP')
                - optional (bool): Whether the property is optional
                - index (bool, optional): Whether to create an index
                And make sure the primary key occurs in the properties list and is not optional.

        Returns:
            str: The complete Cypher statement for creating the edge label, and it's result.

        Example:
            properties = [
                {
                    "name": "id",
                    "type": "STRING",
                    "optional": False,
                    "index": True,
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "optional": True
                },
                // Add more properties as needed
            ]
            execution_result = create_vertex_label_by_json_schema("Person", "id", properties)
        """
        # Validate primary key exists in properties
        primary_prop = next((p for p in properties if p["name"] == primary), None)
        if not primary_prop or primary_prop.get("optional", False):
            properties.append(
                {
                    "name": primary,
                    "type": "STRING",
                    "optional": False,
                }
            )

        # Prepare the JSON structure
        label_json = {
            "label": label,
            "primary": primary,
            "type": "VERTEX",
            "properties": properties,
        }

        # Generate the Cypher statement
        cypher_exec = CypherExecutor()
        return await cypher_exec.validate_and_execute_cypher(
            graph_db_service=graph_db_service,
            cypher_schema=f"CALL db.createVertexLabelByJson('{json.dumps(label_json, ensure_ascii=False)}')",  # noqa: E501
        )


class EdgeLabelAdder(Tool):
    """Tool for generating Cypher statements to create edge labels in TuGraph."""

    def __init__(self):
        super().__init__(
            name=self.create_edge_label_by_json_schema.__name__,
            description=self.create_edge_label_by_json_schema.__doc__ or "",
            function=self.create_edge_label_by_json_schema,
        )

    async def create_edge_label_by_json_schema(
        self,
        graph_db_service: GraphDbService,
        label: str,
        primary: str,
        properties: List[Dict[str, Union[str, bool]]],
        constraints: List[List[str]],
    ) -> str:
        """Generate a TuGraph edge label statement, and then operator the TuGraph database to create
        the labels in the database.
        Field names can only contain letters, numbers, and underscores. The value of the parameters
        should be in English.

        Args:
            label (str): The name of the edge label to create
            primary (str): The name of the primary key field
            properties (List[Dict]): List of property definitions, each containing:
                - name (str): Property name
                - type (str): Property type (e.g., 'STRING', 'INT32')
                - optional (bool): Whether the property is optional
            constraints (List[List[str]]): List of source and target vertex label constraints, which
            presents the direction of the edge.
                It can configure multiple source and target vertex label constraints,
                for example, [["source label", "target label"], ["other source label", "other target
                    label"]]

        Returns:
            str: The complete Cypher statement for creating the edge label, and it's result.

        Example:
            properties = [
                {
                    "name": "type",
                    "type": "STRING",
                    "optional": False
                },
                // Add more properties as needed
            ]
            execution_result = create_edge_label_by_json_schema(
                "KNOWS",
                "id",
                properties,
                [
                    ["Person", "Person"],
                    ["Organization", "Person"]
                ]
            )
        """
        primary_prop = next((p for p in properties if p["name"] == primary), None)
        if not primary_prop or primary_prop.get("optional", False):
            properties.append(
                {
                    "name": primary,
                    "type": "STRING",
                    "optional": False,
                }
            )

        # prepare the JSON structure
        label_json = {
            "label": label,
            "type": "EDGE",
            "properties": properties,
            "constraints": constraints,
        }

        cypher_exec = CypherExecutor()
        return await cypher_exec.validate_and_execute_cypher(
            graph_db_service=graph_db_service,
            cypher_schema=f"CALL db.createEdgeLabelByJson('{json.dumps(label_json, ensure_ascii=False)}')",  # noqa: E501
        )


class CypherExecutor(Tool):
    """Tool for validating and executing TuGraph Cypher schema definitions."""

    def __init__(self):
        super().__init__(
            name=self.validate_and_execute_cypher.__name__,
            description=self.validate_and_execute_cypher.__doc__ or "",
            function=self.validate_and_execute_cypher,
        )

    async def validate_and_execute_cypher(
        self, graph_db_service: GraphDbService, cypher_schema: str
    ) -> str:
        """Validate the TuGraph Cypher and execute it in the TuGraph Database.
        Make sure the input cypher is only the code without any other information including
        ```Cypher``` or ```TuGraph Cypher```.
        This function can only execute one cypher schema at a time.
        If the schema is valid, return the validation results. Otherwise, return the error message.

        Args:
            cypher_schema (str): TuGraph Cypher schema including only the code.

        Returns:
            Validation and execution results.
        """

        try:
            store = graph_db_service.get_default_graph_db()
            store.conn.run(cypher_schema)
            return f"TuGraph 成功运行如下 schema：\n{cypher_schema}"
        except Exception as e:
            prompt = (
                CYPHER_GRAMMER
                + f"""假设你是 TuGraph DB 的管理员，请验证我给你 TuGraph Cypher 指令的正确性。标准不要太严格，只要不和 TuGraph Cypher 语法冲突就行。
    无论你是否验证通过，都应该给出信息反馈。同时，请确保，输入是用于 Create Schema 的 TuGraph Cypher 指令，而不是数据导入的 Cypher 指令。
    你的最终回答是：语法不合规，然后给出错误信息和修改提示。

    如果输入包含多条 Cypher，则返回错误信息和修改提示，以反映输入的 Cypher 有误。

    经过 TuGraph 内置的验证器，得到了执行错误：{str(e)}
            """  # noqa: E501
            )

            message = ModelMessage(payload=cypher_schema, job_id="cypher_validation_id", step=1)

            _model = ModelServiceFactory.create(model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
            response = await _model.generate(
                sys_prompt=prompt,
                messages=[message],
                tool_call_ctx=ToolCallContext(
                    job_id="cypher_validation_id", operator_id="op_id"
                ),
            )
            raise RuntimeError(response.get_payload()) from e


class GraphReachabilityGetter(Tool):
    """Tool for getting the reachability information of the graph database."""

    def __init__(self):
        super().__init__(
            name=self.get_graph_reachability.__name__,
            description=self.get_graph_reachability.__doc__ or "",
            function=self.get_graph_reachability,
        )

    async def get_graph_reachability(self, graph_db_service: GraphDbService) -> str:
        """Get the reachability information of the graph database which can help to understand the
        graph structure.

        Args:
            None args required

        Returns:
            str: The reachability of the graph database in string format

        Example:
            reachability_str = get_graph_reachability()
        """
        query = "CALL dbms.graph.getGraphSchema()"
        store = graph_db_service.get_default_graph_db()
        schema = store.conn.run(query=query)

        edges: List = []
        vertexes: List = []
        for element in json.loads(schema[0][0])["schema"]:
            if element["type"] == "EDGE":
                edges.append(element)
            elif element["type"] == "VERTEX":
                vertexes.append(element)
        if not edges or not vertexes:
            return "The graph database schema was not created yet."

        # check if there are any isolated vertexes
        constraints: Set[str] = set()
        for edge in edges:
            for constraint in edge["constraints"]:
                constraints.add(constraint[0])
                constraints.add(constraint[1])
        vertex_labels = [vertex["label"] for vertex in vertexes]
        isolated_labels = []
        for vertex_label in vertex_labels:
            if vertex_label not in constraints:
                isolated_labels.append(vertex_label)

        # return the reachability information
        return self._format_reachability_info(vertex_labels, edges, isolated_labels)

    def _format_reachability_info(
        self,
        vertex_labels: List[str],
        edges: List[Dict],
        isolated_labels: Optional[List[str]] = None,
    ) -> str:
        """Format the reachability information of the graph database."""
        lines = ["Got the reachability of the graph:"]
        lines.append(f"Vertices: {', '.join(f'({label})' for label in vertex_labels)}")

        edge_lines = [
            f"({cons[0]})-[edge:{edge['label']}]->({cons[1]})"
            for edge in edges
            for cons in edge["constraints"]
        ]
        lines.extend(edge_lines)

        if isolated_labels:
            lines.append(
                "!!! This graph database schema does not have reachability.\n"
                "!!! Isolated vertices found: "
                f"{', '.join(f'({label})' for label in isolated_labels)}"
            )
        else:
            lines.append("After verified, the graph database schema has reachability.")

        return "\n".join(lines)
