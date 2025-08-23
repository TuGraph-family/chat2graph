from app.core.workflow.workflow_generator.mcts_workflow_generator.workflow_generator import MCTSWorkflowGenerator
from app.core.workflow.dataset_synthesis.data_synthesis import DatasetGenerator
from app.core.workflow.dataset_synthesis.dataset_generator.sampling_dataset_generator import SamplingDatasetGenerator
from app.core.workflow.workflow_generator.mcts_workflow_generator.selector import MixedProbabilitySelector
from app.core.workflow.workflow_generator.mcts_workflow_generator.evaluator import LLMEvaluator
from app.core.workflow.workflow_generator.mcts_workflow_generator.expander import LLMExpander
from app.core.toolkit.graph_db.graph_db import GraphDb
from test.resource.init_server import init_server
from app.core.service.graph_db_service import GraphDbService, GraphDbConfig
from app.core.toolkit.graph_db.graph_db_factory import GraphDbFactory
from app.core.common.type import GraphDbType
import json
import asyncio
from pathlib import Path

init_server()
DB_CONFIG = GraphDbConfig( #TODO
    type=GraphDbType.NEO4J,
    name="test",
    desc="test",
    host="192.168.18.219",
    port="7687",
    user="neo4j",
    pwd="xxxx"
)

async def test():
    db_service: GraphDbService = GraphDbService.instance
    for config in db_service.get_all_graph_db_configs():
        if config.name == DB_CONFIG.name:
            db_service.delete_graph_db(config.id)
    
    db_config =db_service.create_graph_db(DB_CONFIG)
    db: GraphDb = GraphDbFactory.get_graph_db(graph_db_type=db_config.type, config=db_config)
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
    workflow_generator.run()
    workflow_generator.log_save()

async def generate_dataset(generator: DatasetGenerator, file_path):
    train_set = await generator.generate("帮我生成一些关于图上的多跳推理相关的问题。", dataset_name="test", size=10)
    print(f"end, train_set={train_set}")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([{"task": row.task, "verifier": row.verifier} for row in train_set.dataset], f, indent=2)
    return train_set
    
if __name__ == "__main__":
    asyncio.run(test())