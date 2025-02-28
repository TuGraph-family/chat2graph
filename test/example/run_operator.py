import matplotlib.pyplot as plt

from app.core.model.job import SubJob
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.service.service_factory import ServiceFactory
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.toolkit import Toolkit
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from test.resource.tool_resource import Query

ServiceFactory.initialize()


def main():
    """Main function to demonstrate Operator usage."""
    # initialize
    toolkit = Toolkit()

    action1 = Action(
        id="search",
        name="Search Knowledge",
        description="Search relevant information from knowledge base",
    )
    action2 = Action(
        id="analyze",
        name="Analyze Content",
        description="Analyze and extract insights from content",
    )
    action3 = Action(
        id="generate",
        name="Generate Response",
        description="Generate response based on analysis",
    )

    search_tool = Query(id="search_tool")
    analyze_tool = Query(id="analyze_tool")

    # set operator properties
    instruction = """
通过查找数据库，分析三国演义中的关键实体，生成对应的实体关系图。(用中文回答)
Answer in Chinese.

输入的数据是三国演义全文，需要从中识别出关键实体类型。这些文本包含了丰富的历史信息，涵盖了人物对话、事件描述、地理位置、时间节点等多个维度的内容。
文本中的实体之间存在复杂的关联关系，需要系统性地进行识别和分类。

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
    """

    context = """
输入文本：
建安七年冬，赤壁之战后，孙刘联盟虽挫败曹操，但天下大局仍未定。刘备在荆州稳固立足，诸葛亮提出“隆中对”，建议占据荆益二州，以图天下。刘备遂决意西进，目光投向益州。

此时，孙权在东吴亦稳固政权，着手发展水师，准备进一步扩张。然而，荆州问题成为孙刘之间潜在的矛盾，孙权遣使与刘备交涉，要求分占荆州部分地盘。

曹操在北方虽受挫，却未气馁，休养生息，整顿内政，削弱地方豪强，强化中央集权。他目光长远，等待时机再次南下。

刘备在荆州得到当地豪强支持，开始实施改革，发展农业，增强军力。诸葛亮主政，制定有利于发展的政策，深受百姓爱戴。

孙权与刘备的关系渐显裂痕，特别是在荆州归属问题上。孙权虽与刘备联盟，心中却对荆州虎视眈眈。

建安八年，刘备进军汉中，与张鲁交战，关羽镇守荆州，威震华夏。诸葛亮在后方运筹帷幄，确保前方战事顺利。

曹操在北方巩固统治，派遣大将张辽驻守合肥，以防孙权北上。孙权与张辽在合肥对峙，双方各有胜负。

建安十二年，刘备攻克汉中，张鲁投降，益州门户大开。诸葛亮建议刘备趁机夺取益州，刘备采纳，遣诸葛亮留守荆州，自率大军西进。

建安十三年，刘备入益州，刘璋不敌，献城投降。至此，刘备占据益州，势力大增。诸葛亮留守荆州，确保东吴无隙可乘。

孙权见刘备势力日盛，心中不安，暗中筹备，等待时机与刘备决裂。而曹操在北方，亦在积蓄力量，等待南下的机会。

三国鼎立之势，初现端倪，各路英雄在乱世中书写自己的传奇。刘备、孙权、曹操，三人之间的博弈，才刚刚开始。

    """

    # itialize reasoner
    reasoner = DualModelReasoner()
    operator_config = OperatorConfig(
        instruction=instruction,
        actions=[action1],
        threshold=0.7,
        hops=2,
    )
    operator = Operator(config=operator_config)

    # add actions to toolkit
    toolkit_service: ToolkitService = ToolkitService.instance or ToolkitService()
    toolkit_service.add_action(
        action=action1,
        next_actions=[(action2, 0.9)],
        prev_actions=[],
    )
    toolkit_service.add_action(
        action=action2,
        next_actions=[(action3, 0.8)],
        prev_actions=[(action1, 0.9)],
    )
    toolkit_service.add_action(
        action=action3,
        next_actions=[],
        prev_actions=[(action2, 0.8)],
    )

    # add tools to toolkit
    toolkit_service.add_tool(tool=search_tool, connected_actions=[(action1, 0.9)])
    toolkit_service.add_tool(tool=analyze_tool, connected_actions=[(action2, 0.9)])

    # execute operator (with minimal reasoning rounds for testing)
    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context=context,
    )
    result = operator.execute(reasoner=reasoner, job=job)

    print(f"Operator execution result:\n{result}\n")
    print("Operator execution completed successfully")

    plt.show()


if __name__ == "__main__":
    main()
