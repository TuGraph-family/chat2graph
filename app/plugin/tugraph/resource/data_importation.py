import json
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.common.system_env import SystemEnv
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.toolkit.tool import Tool
from app.plugin.tugraph.tugraph_store import get_tugraph

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
        """Get the schema of a graph database.

        Args:
            None args required

        Returns:
            str: The schema of the graph database in string format

        Example:
            schema_str = get_schema()
        """
        query = "CALL dbms.graph.getGraphSchema()"
        sstore = get_tugraph()
        schema = sstore.conn.run(query=query)

        result = f"{SCHEMA_BOOK}\n\n查询成功，得到当下的图 schema：\n" + json.dumps(
            json.loads(schema[0][0])["schema"], indent=4, ensure_ascii=False
        )

        return result


class CypherExecutor(Tool):
    """Tool for validating and executing TuGraph Cypher schema definitions."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.validate_and_execute_cypher.__name__,
            description=self.validate_and_execute_cypher.__doc__ or "",
            function=self.validate_and_execute_cypher,
        )

    async def validate_and_execute_cypher(self, cyphers: List[str], **kargs) -> str:
        """Validate the TuGraph Cypher and execute it in the TuGraph Database.
        Make sure the input cypher is only the code without any other information including ```Cypher``` or ```TuGraph Cypher```.
        This function can only execute one cypher schema at a time.
        If the schema is valid, return the validation results. Otherwise, return the error message.

        Args:
            cypher (str): TuGraph Cypher including only the code.

        Returns:
            Validation and execution results.
        """  # noqa: E501

        print("\n".join(cyphers))
        try:
            store = get_tugraph()
            for cypher in cyphers:
                print(f"result: {(store.conn.run(cypher)[0])}")
            return f"TuGraph 导入数据成功，成功运行如下指令：\n{'  '.join(cyphers)}"
        except Exception as e:
            prompt = (
                SCHEMA_BOOK
                + f"""假设你是 TuGraph DB 的管理员，经过数据库执行，得到的语句出现了报错，你需要给我信息反馈。

标准不要太严格，只要不和 TuGraph Cypher 语法冲突就行。最好是具体的修改提示，而不是泛泛而谈，只谈数据导入的问题。schema 是无法修改的。
我只能修改调用函数的参数，不能修改和查看调用函数的内部逻辑、graph schema 和数据库已有的数据。
信息反馈的部分中，需要返回错误信息，针对调用函数的参数的修改提示。

经过 TuGraph 内置的验证器，得到了执行错误：
{str(e)}

原始的执行语句（这些语句是由调用函数的参数转化而来的）：
{cyphers}

调用函数的参数：
{kargs}

你的最终回答是：由函数拼接出的 Cypher 语法不合规，然后给出错误信息和针对调用函数的参数的修改提示，而不仅仅是只传递错误信息。
"""  # noqa: E501
            )

            message = ModelMessage(payload=cypher, job_id="validate_and_execute_cypher_id", step=1)

            _model = ModelServiceFactory.create(model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
            response = await _model.generate(sys_prompt=prompt, messages=[message])
            raise Exception(response.get_payload()) from e


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
            - Use the pingyin (by CamelCase naming) for the field if it is related to the identity
                instead of the number (e.g., "LiuBei" for person_id, instead of "1")

        Processing Mechanism:
            - Data is processed one triple at a time (source node, target node, and their relationship)
            - For each relationship, the function will:
                1. Find matching source and target entities
                2. Create/update the source node
                3. Create/update the target node
                4. Create/update the relationship

        Args:
            source_label (str): Label of the source node (e.g., "Person"), defined in the graph schema
            source_primary_key (str): Primary key of the source node (e.g., "id")
            source_properties (Dict[str, Any]): Properties of the source node, including:
                - some_primary_key_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - Other related fields as defined in schema
            target_label (str): Label of the target node, defined in the graph schema
            target_primary_key (str): Primary key of the target node
            target_properties (Dict[str, Any]): Properties of the target node, including:
                - some_primary_key_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - Other related fields as defined in schema
            relationship_label (str): Label of the relationship, defined in the graph schema
            relationship_properties (Dict[str, Any]): Properties of the relationship, including:
                - some_primary_key_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - Other related fields as defined in schema

        Returns:
            str: Summary of the import operation, including counts of entities and relationships
                processed, created, and updated.
        """  # noqa: E501

        def format_date(value: str) -> str:
            """Format date value to ensure it has a leading zero in the year."""
            # match date format like "XXX-XX-XX" or "XXX-XX-XXTxx:xx:xxZ"
            date_pattern = r"^(\d{3})-(\d{2})-(\d{2})(T[\d:]+Z)?$"
            match = re.match(date_pattern, value)
            if match:
                year = match.group(1)
                if len(year) == 3:
                    # add leading zero to three-digit year
                    time_part = match.group(4) or ""
                    return f"0{year}-{match.group(2)}-{match.group(3)}{time_part}"
            return value

        def format_property(key: str, value: Any) -> str:
            """Format property key-value pair for Cypher query."""
            if value is None:
                return f"{key}: null"
            elif isinstance(value, int | float):
                return f"{key}: {value}"
            else:
                str_value = str(value)
                if (
                    isinstance(str_value, str)
                    and str_value
                    and (key in ["date", "start_date", "end_date", "start_time"])
                ):
                    str_value = format_date(str_value)
                str_value = str_value.replace("'", "\\'")
                return f"{key}: '{str_value}'"

        def generate_property_string(properties: Dict[str, Any]) -> str:
            """Generate formatted property string for Cypher query."""
            return ", ".join(format_property(k, v) for k, v in properties.items())

        # process source node
        # source_properties["id"] = str(uuid4())
        source_props_str = generate_property_string(source_properties)
        source_statement = f"CALL db.upsertVertex('{source_label}', [{{{source_props_str}}}])"

        # process target node
        # target_properties["id"] = str(uuid4())
        target_props_str = generate_property_string(target_properties)
        target_statement = f"CALL db.upsertVertex('{target_label}', [{{{target_props_str}}}])"

        # process relationship
        rel_props = {
            **relationship_properties,
            "source_node": source_properties[source_primary_key],
            "target_node": target_properties[target_primary_key],
        }
        rel_props_str = generate_property_string(rel_props)

        rel_statement = (
            f"CALL db.upsertEdge('{relationship_label}', "
            f"{{type: '{source_label}', key: 'source_node'}}, "
            f"{{type: '{target_label}', key: 'target_node'}}, "
            f"[{{{rel_props_str}}}])"
        )

        cypher_executor = CypherExecutor()
        return await cypher_executor.validate_and_execute_cypher(
            [source_statement, target_statement, rel_statement],
            source_label=source_label,
            source_primary_key=source_primary_key,
            source_properties=source_properties,
            target_label=target_label,
            target_primary_key=target_primary_key,
            target_properties=target_properties,
            relationship_label=relationship_label,
            relationship_properties=relationship_properties,
        )


SCHEMA_BOOK = """
# 图数据库 Schema 指南 (LLM 友好版)

本指南旨在帮助你理解和设计图数据库的 Schema，以便 LLM (语言模型) 更好地理解图数据的结构。

## 1. 顶点 (Vertex) 定义 (实体定义)

在图数据库中，**顶点 (Vertex)** 代表 **实体 (Entity)**，是图结构中的基本单元。 每个 **顶点类型** 的定义描述了具有相同特征的实体的结构。

### 1.1. 顶点类型要素

每个 **顶点类型** 定义包含以下关键要素：

- **标签 (Label):**
    - **定义:**  **标签 (Label)** 是 **顶点类型** 的名称或标识符。它用于区分不同类型的实体。
    - **示例:** 例如，`"Person"` (人), `"Event"` (事件), `"Location"` (地点), `"Organization"` (组织) 等都是常见的 **顶点标签 (Vertex Label)**。
    - **JSON Schema 示例:** 在提供的 JSON Schema 中，`"label": "Person"`  定义了一个 **顶点类型** 的标签为 `"Person"`。

- **主键 (Primary Key):**
    - **定义:**  **主键 (Primary Key)** 是 **顶点类型** 的唯一标识属性。它用于在图中唯一地识别每个顶点实例。
    - **重要性:**  **主键** 必须是唯一的，并且通常选择一个核心属性作为 **主键**。
    - **示例:**  例如，`"person_id"` 可以作为 `"Person"` **顶点类型** 的 **主键**， `"event_id"` 可以作为 `"Event"` **顶点类型** 的 **主键**。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"primary": "person_id"`  指定 `"person_id"` 属性为 `"Person"` **顶点类型** 的 **主键**。

- **属性 (Properties):**
    - **定义:**  **属性 (Properties)** 描述了 **顶点** 的特征或信息。每个 **顶点类型** 可以包含多个 **属性**。
    - **属性要素:**  每个 **属性** 定义包含以下子要素：
        - **名称 (name):**  **属性** 的标识符，例如 `"name"`, `"description"`, `"occurrence_time"` 等。
        - **数据类型 (type):**  **属性** 存储的数据类型，例如 `"STRING"` (字符串), `"INTEGER"` (整数), `"DATE"` (日期) 等。
        - **可选性 (optional):**  标记 **属性** 是否可以为空。`true` 表示可选，`false` 表示必填。
        - **索引 (index):**  标记 **属性** 是否创建索引以优化查询性能。`true` 表示创建索引。
        - **唯一性 (unique):**  标记 **属性** 值在同类型顶点中是否唯一。`true` 表示唯一。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"properties": [...]`  数组定义了 **顶点类型** 的所有 **属性**，例如 `"name": {"name": "name", "type": "STRING", "optional": false}` 定义了一个名为 `"name"`，类型为 `"STRING"`，非可选的属性。

## 2. 边 (Edge) 定义 (关系定义)

在图数据库中，**边 (Edge)** 代表 **关系 (Relationship)**，用于连接不同的 **顶点 (Vertex)**，表达实体之间的联系。 每个 **边类型** 的定义描述了具有相同联系类型的关系结构。

### 2.1. 边类型要素

每个 **边类型** 定义包含以下关键要素：

- **标签 (Label):**
    - **定义:**  **标签 (Label)** 是 **边类型** 的名称或标识符。它用于区分不同类型的关系。
    - **示例:** 例如， `"Relationship"` (关系) 可以作为一个通用的 **边标签 (Edge Label)**， 或者更具体的标签如 `"LOCATED_IN"` (位于...), `"WORKS_FOR"` (工作于...) 等。
    - **JSON Schema 示例:** 在提供的 JSON Schema 中，`"label": "Relationship"`  定义了一个 **边类型** 的标签为 `"Relationship"`。

- **约束 (Constraints):**
    - **定义:**  **约束 (Constraints)**  定义了 **边类型** 可以连接的 **顶点类型** 对。它限制了关系的连接对象类型。
    - **重要性:**  **约束** 确保了关系的有效性和数据一致性。
    - **注意事项:**  **约束** 可以包含多个 **顶点类型** 对，表示 **边类型** 可以连接的多种 **顶点类型** 组合。并且，边的连接方向是有序的，即 `(source, target)` 和 `(target, source)` 是不同的。
    - **示例:**  例如，`"Relationship"`  **边类型** 的 **约束**  `[["Person", "Event"], ["Event", "Location"], ["Person", "Organization"]]` 表示：
        - `"Relationship"` 边可以连接 `"Person"` 类型的顶点 和 `"Event"` 类型的顶点。
        - `"Relationship"` 边可以连接 `"Event"` 类型的顶点 和 `"Location"` 类型的顶点。
        - `"Relationship"` 边可以连接 `"Person"` 类型的顶点 和 `"Organization"` 类型的顶点。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"constraints": [[ "Person", "Event" ], ... ]`  定义了 `"Relationship"` **边类型** 的 **约束**。

- **属性分离 (Detach Property):**
    - **定义:**  `"detach_property": true`  标记 **边类型** 的 **属性** 是否可以独立于边本身存储。
    - **用途:**  `detach_property`  通常用于优化存储和性能，尤其是在属性数据量较大时。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"detach_property": true` 表示启用了属性分离。

- **属性 (Properties):**
    - **定义:**  **属性 (Properties)** 描述了 **边** 的特征或信息。 每个 **边类型** 也可以包含多个 **属性**。
    - **属性要素:**  **边属性** 的结构和要素与 **顶点属性** 相同，包括 **名称 (name)**, **数据类型 (type)**, **可选性 (optional)** 等。
    - **示例:**  例如，`"relationship_id"`, `"description"`, `"strength"`, `"type"` 可以作为 `"Relationship"` **边类型** 的 **属性**。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"properties": [...]`  数组定义了 **边类型** 的所有 **属性**，例如 `"type": {"name": "type", "type": "STRING", "optional": false}` 定义了一个名为 `"type"`，类型为 `"STRING"`，非可选的属性。

"""  # noqa: E501
