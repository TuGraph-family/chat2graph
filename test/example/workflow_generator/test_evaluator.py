import asyncio

from app.core.workflow.dataset_synthesis.utils import load_workflow_train_dataset
from app.core.workflow.workflow_generator.mcts_workflow_generator.evaluator import LLMEvaluator


async def main():
    # evaluator = LLMEvaluator()
    # optimized_path = "test/example/workflow_generator/workflow_space/test_just"
    # dataset_path = "test/example/workflow_generator/data.json"
    # dataset = load_workflow_train_dataset(task_desc="你的主要任务是完成图数据库的查询任务", path=dataset_path)
    # await evaluator.evaluate_workflow(
    #     optimized_path=optimized_path,
    #     round_num=1,
    #     parent_round=-1,
    #     dataset=dataset.dataset[:5],
    #     modifications=[
    #     ]
    # )
    
    # result = await evaluator._llm_scoring(
    #     question="Which companies have a business type of 'Research Institute' and have invested in companies located in 'Piliscsaba'?",
    #     expected_answer="The company 'Jenkins-Batz' (ID: 7783) has a business type of 'Research Institute' and has invested in 'Stanton PLC', which is located in 'Piliscsaba'.",
    #     model_output="**Schema Inference Status**: Success  \n**Inferred Schema Elements**:  \n- **Node Labels**: `Company`, `Person`, `Account`, `Loan`  \n- **Relationship Types**: `INVEST`, `TRANSFER`, `REPAY`, `WITHDRAW`, `DEPOSIT`  \n- **Company Attributes**:  \n  - Business Type: `business` (e.g., `\"Research Institute\"`, `\"Theater Production\"`)  \n  - Location: `city`, `country`  \n  - Other: `companyName`, `description`, `url`, `id`, `isBlocked`, `createTime`  \n- **Person Attributes**:  \n  - Name: `personName`  \n  - Location: `city`, `country`  \n- **Account Attributes**:  \n  - Type: `accountType`  \n  - Other: `nickname`, `phonenum`, `email`  \n- **Loan Attributes**:  \n  - Relationships: `DEPOSIT`  \n\n**Query Used for Inference**:  \n```cypher\nMATCH (r:Company {business: 'Research Institute'})-[rel:INVEST]->(c:Company {city: 'Piliscsaba'}) RETURN r, rel, c\n```\n\n**Validation Result**: Schema elements were successfully validated through query execution, identifying a `\"Research Institute\"` company (`Jenkins-Batz`) investing in a company located in `\"Piliscsaba\"`.\n"
    # )
    # print(f"result:{result}\n")
    # # await evaluator.evaluate_workflow(
    # #     optimized_path=optimized_path,
    # #     round_num=2,
    # #     parent_round=1,
    # #     dataset=dataset.dataset[:1],
    # #     modifications=[
    # #       "Modified `basic_operator` to specialize in query intention understanding and graph schema alignment.",
    # #       "Added `graph_schema_validation_operator` to validate query intentions against the graph schema before execution.",
    # #       "Added `multi_hop_reasoning_operator` to support complex reasoning across multiple entities and relationships in the graph.",
    # #       "Modified the `basic Expert` to be more specialized in query understanding and schema mapping.",
    # #       "Added a new expert called `Schema Validation Expert` to handle schema validation tasks independently.",
    # #       "Introduced a new expert named `Multi-Hop Reasoning Expert` dedicated to complex path tracing and reasoning tasks.",
    # #       "Split responsibilities across experts to ensure each focuses on a single domain task, improving modularity and performance."
    # #     ]
    # # )
    dataset_paths = [
        # "test/example/workflow_generator/data_50.json",
        "test/example/workflow_generator/data_100.json"
    ]
    optimized_path = "test/example/workflow_generator/workflow_space/test_just"
    
    for dataset in dataset_paths:
        await eval(dataset, optimized_path, data_start=70, data_end=80, data_size=10, round_start=107)

async def eval(dataset_path: str, optimized_path: str, data_start: int, data_end: int, data_size: int, round_start: int):
    evaluator = LLMEvaluator(need_reflect=False)
    dataset = load_workflow_train_dataset(task_desc="你的主要任务是完成图数据库的查询任务", path=dataset_path)
    round = round_start
    for i in range(data_start, data_end, data_size):
        await evaluator.evaluate_workflow(
            optimized_path=optimized_path,
            round_num=round,
            parent_round=-1,
            dataset=dataset.data[i:i+data_size],
            modifications=[
            ]
        )
        round += 1




if __name__ == "__main__":
    asyncio.run(main())