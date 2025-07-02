from typing import List, Tuple

from app.core.toolkit.tool import Tool

TUGRAPH_DOC = [
    """
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
""",
    """
### 1.2. 数据类型

TuGraph支持多种可用于属性的数据类型。具体支持的数据类型如下：

| **数据类型** | **最小值**          | **最大值**          | **描述**                            |
| ------------ | ------------------- | ------------------- | ----------------------------------- |
| BOOL         | false               | true                | 布尔值                              |
| INT8         | -128                | 127                 | 8位整型                          |
| INT16        | -32768              | 32767               | 16位整型                         |
| INT32        | - 2^31              | 2^31 - 1            | 32位整型                         |
| INT64        | - 2^63              | 2^63 - 1            | 64位整型                         |
| DATE         | 0000-00-00          | 9999-12-31          | "YYYY-MM-DD" 格式的日期             |
| DATETIME     | 0000-00-00 00:00:00.000000 | 9999-12-31 23:59:59.999999 | "YYYY-MM-DD HH:mm:ss[.ffffff]" 格式的日期时间 |
| FLOAT        |                     |                     | 32位浮点数                       |
| DOUBLE       |                     |                     | 64位浮点数                       |
| STRING       |                     |                     | 不定长度的字符串                    |
| BLOB         |                     |                     | 二进制数据（在输入输出时使用Base64编码） |
| POINT        |                     |                     | EWKB格式数据，表示点              |
| LINESTRING   |                     |                     | EWKB格式数据，表示线              |
| POLYGON      |                     |                     | EWKB格式数据，表示面(多边形)       |
| FLOAT_VECTOR |                     |                     | 包含32位浮点数的动态向量               |
""",  # noqa: E501
]

TUGRAPH_REF = ["TuGraph-Cpyher语法书", "TuGraph图模型说明-数据类型"]

INTERNET_DOC = [
    """
Neo4j是一款流行的图数据库，它使用Cypher查询语言来操作和查询图数据。在Python中，我们可以使用Neo4j的官方驱动程序或第三方库（如py2neo）来与数据库进行交互。然而，当我们执行某些复杂的Cypher查询时，有时会发现结果被截断或不完整显示。下面将介绍可能导致此问题的原因，并提供相应的解决方案。
1.原因分析
该问题通常是由以下原因之一引起的：
-默认限制：Neo4j驱动程序在执行Cypher查询时，默认会对结果进行限制。这个限制通常是为了避免查询结果过大导致性能问题。因此，在显示结果时，驱动程序只会显示一部分数据，而不是全部。
-结果截断：如果查询结果非常庞大，超出了驱动程序的限制，结果将被截断并丢失一部分数据。这可能会导致我们无法看到完整的结果。
2.解决方案
根据原因，下面提供几种解决方案：
-增加限制：如果您确定查询结果不会导致性能问题，可以通过设置Neo4j驱动程序的配置选项来增加默认限制。例如，对于官方驱动程序，您可以使用`session.run`方法的`max_records`参数来增加限制。但请注意，增加限制可能会影响性能，因此请根据具体情况谨慎使用。
-使用分页查询：如果查询结果仍然超出限制，您可以考虑使用分页查询来获取完整的结果。通过在Cypher查询中使用`SKIP`和`LIMIT`子句，您可以按照指定的步长逐渐获取结果集的不同部分。然后，您可以在Python中使用循环来合并所有分页结果，并显示完整的结果。
-导出到文件：如果以上方法仍无法满足您的需求，您可以将查询结果导出到文件中进行查看。Neo4j驱动程序通常提供将结果导出为CSV或其他格式的功能。您可以将结果导出为文件，然后在Python中读取和查看结果。
3.检查解决方案
根据您的需求选择合适的解决方案后，重新运行查询并检查是否成功显示完整的结果。如果结果仍然不完整，请确保您已正确设置驱动程序的配置选项或正确实现分页查询。如果您选择将结果导出到文件，请确保文件中包含完整的结果。
当在Python中使用Neo4j图数据库执行Cypher查询时，有时会遇到结果不完整显示的问题。这是由于默认限制或结果截断导致的。通过增加限制、使用分页查询或将结果导出到文件，我们可以解决这个问题，并获得完整的Cypher查询结果。根据具体需求，请选择适合您的解决方案，以便在Python中正常查看和处理Neo4j查询结果。
分享快讯到朋友圈
"""  # noqa: E501
]

INTERNET_REF = [
    "https://cloud.tencent.com/developer/news/1294500",
]


class KnowledgeBaseRetriever(Tool):
    """Tool for retrieving document content from knowledge base."""

    def __init__(self):
        super().__init__(
            name=self.knowledge_base_search.__name__,
            description=self.knowledge_base_search.__doc__ or "",
            function=self.knowledge_base_search,
        )

    async def knowledge_base_search(self, question: str) -> Tuple[List[str], List[str]]:
        """Retrive a list of related contents and a list of their reference name from knowledge
        base given the question.

        Args:
            question (str): The question asked by user.

        Returns:
            (List[str], List[str]): The list of related contents and the list of reference name.
        """

        return TUGRAPH_DOC, TUGRAPH_REF


class InternetRetriever(Tool):
    """Tool for retrieving webpage contents from Internet."""

    def __init__(self):
        super().__init__(
            name=self.internet_search.__name__,
            description=self.internet_search.__doc__ or "",
            function=self.internet_search,
        )

    async def internet_search(self, question: str) -> Tuple[List[str], List[str]]:
        """Retrive a list of related webpage contents and a list of their URL references from
        Internet given the question.

        Args:
            question (str): The question asked by user.

        Returns:
            Tuple[List[str], List[str]]: The list of related webpage contents and the list of URL
            references.
        """

        return INTERNET_DOC, INTERNET_REF
