from app.core.workflow.workflow_generator.mcts_workflow_generator.core import MCTSWorkflowGenerator
from app.core.workflow.dataset_synthesis.generator import DatasetGenerator
from app.core.workflow.dataset_synthesis.generator import SamplingDatasetGenerator
from app.core.workflow.workflow_generator.mcts_workflow_generator.selector import MixedProbabilitySelector
from app.core.workflow.workflow_generator.mcts_workflow_generator.evaluator import LLMEvaluator
from app.core.workflow.workflow_generator.mcts_workflow_generator.expander import LLMExpander
from test.example.workflow_generator.utils import register_and_get_graph_db
from test.resource.init_server import init_server
import json
import asyncio
from pathlib import Path

init_server()

async def test():
    db = register_and_get_graph_db()
    dataset_generator: DatasetGenerator = SamplingDatasetGenerator(graph_db=db)

    data_file_path = Path(__file__).resolve().parent / "data.json"
    print(data_file_path)
    if Path.exists(data_file_path):
        print("loading data...")
        dataset = dataset_generator.load(task_desc="你的主要职责是解决关于图数据库的各种问题，包括实体查询、多跳推理等等", path=data_file_path)
    else:
        dataset = await generate_dataset(generator=dataset_generator, file_path=data_file_path)
    # # test_get_db_schema(generator=dataset_generator)
    # # test_get_random_subgraph(generator=dataset_generator)
    # await test_generate_dataset(generator=dataset_generator)
    selector = MixedProbabilitySelector()
    expander = LLMExpander()
    evaluator = LLMEvaluator()
    workflow_generator = MCTSWorkflowGenerator(
        db=db, 
        dataset=dataset,
        selector= selector,
        expander=expander,
        evaluator=evaluator,
        max_rounds=5,
        validate_rounds=5,
        optimized_path=Path(__file__).resolve().parent / "workflow_space",
        sample_size=5,
        max_retries=5
        )
    await workflow_generator.run()
    workflow_generator.log_save()

async def generate_dataset(generator: DatasetGenerator, file_path):
    train_set = await generator.generate("帮我生成一些关于图上的多跳推理相关的问题。", dataset_name="test", size=10)
    print(f"end, train_set={train_set}")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([row.model_dump() for row in train_set.dataset], f, indent=2, ensure_ascii=False)
    return train_set
    
if __name__ == "__main__":
    asyncio.run(test())