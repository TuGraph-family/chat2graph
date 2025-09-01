from app.core.workflow.dataset_synthesis.generator import DatasetGenerator
from app.core.workflow.dataset_synthesis.generator import SamplingDatasetGenerator
from app.core.workflow.dataset_synthesis.sampler import SubGraphSampler, EnhancedSubgraphSampler, SimpleRandomSubGraphSampler
from test.resource.init_server import init_server
from test.example.workflow_generator.utils import register_and_get_graph_db
import json
import asyncio

init_server()

async def test():
    db = register_and_get_graph_db()
    dataset_generator: DatasetGenerator = SamplingDatasetGenerator(
        graph_db=db, 
        sampler_cls=EnhancedSubgraphSampler,
        max_depth=2,
        max_noeds=10,
        max_edges=20,
        )
    
    await test_generate_dataset(generator=dataset_generator)


async def test_generate_dataset(generator: DatasetGenerator):
    train_set = await generator.generate("帮我生成一些关于图上的多跳推理相关的问题。", dataset_name="test", size=30)
    print(f"end, train_set={train_set}")
    import time
    dataset_name = "data" + str(int(time.time())) + ".json"
    with open(dataset_name, "w", encoding="utf-8") as f:
        json.dump([{"task": row.task, "verifier": row.verifier} for row in train_set.dataset], f, indent=2, ensure_ascii=False)
    
if __name__ == "__main__":
    asyncio.run(test())