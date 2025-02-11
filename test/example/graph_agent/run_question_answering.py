import asyncio

from app.agent.graph_agent.question_answering import get_question_answering_workflow
from app.agent.job import SubJob
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner

QUESTION = """
我在执行Cypher语句
CALL db.createVertexLabelByJson('{
    "label": "州",
    "primary": "state",
    "type": "VERTEX",
    "properties": [
        {
            "name": "state",
            "type": "INT12"
        }
    ]
}');
的时候，遇到报错：执行失败 unknown keyword str: [INT12]，
请问原因是什么，该如何修改？
"""


async def main():
    """Main function"""
    workflow = get_question_answering_workflow()

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context=QUESTION,
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
