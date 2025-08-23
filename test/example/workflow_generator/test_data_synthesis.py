from app.core.workflow.dataset_synthesis.data_synthesis import DatasetGenerator
from app.core.workflow.dataset_synthesis.dataset_generator.sampling_dataset_generator import SamplingDatasetGenerator
from app.core.toolkit.graph_db.graph_db import GraphDb
from test.resource.init_server import init_server
from app.core.service.graph_db_service import GraphDbService, GraphDbConfig
from app.core.toolkit.graph_db.graph_db_factory import GraphDbFactory
from app.core.common.type import GraphDbType
import json
import asyncio

init_server()
DB_CONFIG = GraphDbConfig( #TODO
    type=GraphDbType.NEO4J,
    name="test",
    desc="test",
    host="192.168.18.219",
    port="7687",
    user="neo4j",
    pwd="xxxxxx"
)

async def test():
    db_service: GraphDbService = GraphDbService.instance
    for config in db_service.get_all_graph_db_configs():
        if config.name == DB_CONFIG.name:
            db_service.delete_graph_db(config.id)
    
    db_config =db_service.create_graph_db(DB_CONFIG)
    db: GraphDb = GraphDbFactory.get_graph_db(graph_db_type=db_config.type, config=db_config)
    dataset_generator: DatasetGenerator = SamplingDatasetGenerator(graph_db=db)
    
    await test_generate_dataset(generator=dataset_generator)


async def test_generate_dataset(generator: DatasetGenerator):
    train_set = await generator.generate("帮我生成一些关于图上的多跳推理相关的问题。", dataset_name="test", size=30)
    print(f"end, train_set={train_set}")
    import time
    dataset_name = "data" + str(int(time.time())) + ".json"
    with open(dataset_name, "w", encoding="utf-8", ensure_ascii=False) as f:
        json.dump([{"task": row.task, "verifier": row.verifier} for row in train_set.dataset], f, indent=2)
    
if __name__ == "__main__":
    asyncio.run(test())