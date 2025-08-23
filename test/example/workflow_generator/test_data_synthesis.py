import asyncio
import json
import time

from app.core.workflow.dataset_synthesis.generator import DatasetGenerator, SamplingDatasetGenerator
from app.core.workflow.dataset_synthesis.sampler import (
    RandomWalkSampler,
)
from test.example.workflow_generator.utils import register_and_get_graph_db
from test.resource.init_server import init_server

init_server()


async def test_indentify_strategy(generator: SamplingDatasetGenerator):
    strategy = await generator.identify_strategy("你的主要任务是对用户提出的图数据库查询需求进行响应，完成图数据库查询任务")
    assert(strategy == "query")
    strategy = await generator.identify_strategy("你的任务是查询并定期清理数据库中不满足条件的数据")
    assert(strategy == "mixed")
    strategy = await generator.identify_strategy("你的主要任务是将数据从数据源（CSV、text等）导入图数据库")
    assert(strategy == "non-query")

async def test_generate_dataset(generator: DatasetGenerator):
    train_set = await generator.generate("你的主要任务是对用户提出的图数据库查询需求进行响应，完成图数据库查询任务", dataset_name="test", size=30)
    print(f"end, train_set={train_set}")

    dataset_name = "data" + str(int(time.time())) + ".json"
    with open(dataset_name, "w", encoding="utf-8") as f:
        json.dump([row.model_dump() for row in train_set.dataset], f, indent=2, ensure_ascii=False)
    

async def test():
    db = register_and_get_graph_db()
    dataset_generator: DatasetGenerator = SamplingDatasetGenerator(
        graph_db=db, 
        strategy="query",
        sampler_cls=RandomWalkSampler,
        max_depth=7,
        max_noeds=15,
        max_edges=30,
        nums_per_subgraph=5,
        )
    tests = [
        (test_generate_dataset, [DatasetGenerator]),
        # (test_indentify_strategy, [SamplingDatasetGenerator]),
    ]

    for test_func, allow_types in tests:
        for t in allow_types:
            if isinstance(dataset_generator, t):
                await test_func(dataset_generator)
    # await test_generate_dataset(generator=dataset_generator)

if __name__ == "__main__":
    asyncio.run(test())
