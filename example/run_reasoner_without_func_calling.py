import asyncio

from app.agent.job import Job
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator import Operator, OperatorConfig


async def main():
    """Main function."""
    graph_modeling_task = """
从原始文本中识别和提取关键实体类型，为后续的图数据库模型构建奠定基础。(用中文回答)
"""
    graph_modeling_context = """
输入的数据是三国演义全文，需要从中识别出关键实体类型。这些文本包含了丰富的历史信息，涵盖了人物对话、事件描述、地理位置、时间节点等多个维度的内容。文本中的实体之间存在复杂的关联关系，需要系统性地进行识别和分类。
Knowledge:
在文学文本的实体识别过程中，需要注意以下几点：
1. 命名实体识别规则
  ○ 人名通常伴随着称号、职位或动作描述
  ○ 地名常与方位词、行政区划词相连
  ○ 时间词通常包含具体的年号、季节或时辰
  ○ 事件名往往与特定的动词或结果描述相关联
2. 文本特征
  ○ 同一实体可能有不同的指代方式（别名、尊称等）
  ○ 实体提及可能是显式或隐式的
  ○ 上下文对实体类型判断至关重要
Actions:
读取文本内容 -next-> 识别关键实体类型
Tools:
1. text_content_loader
描述: 加载并解析源文本内容
输入: file_path, encoding_type
输出: text_content(string)
2. entity_type_extractor
描述: 从文本中识别和提取关键实体类型
输入: text_content(string), extraction_rules(dict)
输出: entity_types(list)
Scratchpad:
输入文本示例：
建安七年春，曹操率军南下。时刘备驻守新野，闻曹操将至，召诸葛亮商议军情。亮曰：“曹操兵强粮足，不可与战，宜退保川口，观机而动。”备从之，遂退守川口。
次日，曹操兵至，见新野空虚，乃进兵攻川口。备使关公出战，不敌，退入川口。操兵久不动，备乃引兵出，与操军交战，大败而走。操兵追至川口，备急闭门守之，城中人马皆惊恐。
城中人马皆惊恐，备曰：“吾有诈，可破之。”遂开门，大呼而出，操兵大败。备乘胜追击，操军大溃，曹操自走脱。备收其军器，仓库，军民无不欢喜。
"""

    reasoner = DualModelReasoner()

    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context=graph_modeling_context,
    )
    operator = Operator(
        config=OperatorConfig(
            instruction=graph_modeling_task,
            actions=[],
        )
    )
    task = Task(job=job, operator=operator)

    await reasoner.infer(task=task)


if __name__ == "__main__":
    asyncio.run(main())
