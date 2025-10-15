import asyncio
import json
from pathlib import Path

from app.core.workflow.dataset_synthesis.generator import DatasetGenerator, SamplingDatasetGenerator
from app.core.workflow.dataset_synthesis.utils import load_workflow_train_dataset
from app.core.workflow.workflow_generator.mcts_workflow_generator.core import MCTSWorkflowGenerator
from app.core.workflow.workflow_generator.mcts_workflow_generator.evaluator import LLMEvaluator
from app.core.workflow.workflow_generator.mcts_workflow_generator.expander import LLMExpander
from app.core.workflow.workflow_generator.mcts_workflow_generator.selector import (
    MixedProbabilitySelector,
)
from test.example.workflow_generator.utils import register_and_get_graph_db
from test.resource.init_server import init_server

init_server()

async def test():
    # 1. 注册图数据库相关的信息，请查看test/example/workflow_generator/utils.py
    db = register_and_get_graph_db()
    dataset_generator: DatasetGenerator = SamplingDatasetGenerator(graph_db=db)

    # 2. 获取数据集：如果指定的数据集已经存在，则直接加载；否则，通过数据合成的方式合成数据集
    data_file_path = Path(__file__).resolve().parent / "data.json"
    print(data_file_path)
    if Path.exists(data_file_path):
        print("loading data...")
        dataset = load_workflow_train_dataset(task_desc="你的主要职责是解决关于图数据库的各种问题，包括实体查询、多跳推理等等", path=data_file_path)
    else:
        dataset = await generate_dataset(generator=dataset_generator, file_path=data_file_path)

    # 3. 定义mcts搜索所需的组件，包括：selector、expander、evaluator
    selector = MixedProbabilitySelector()
    expander = LLMExpander()
    evaluator = LLMEvaluator()
    
    # 4. 定义mcts搜索框架
    workflow_generator = MCTSWorkflowGenerator(
        db=db, 
        dataset=dataset, 
        selector= selector, 
        expander=expander, 
        evaluator=evaluator,
        max_rounds=20,
        optimized_path=Path(__file__).resolve().parent / "workflow_space",
        top_k=5,
        max_retries=5,
        optimize_grain=None,
        init_template_path="test/example/workflow_generator/graph_basic.yml"
        )

    # 5. mcts主流程入口，开始进行工作流生成与优化
    await workflow_generator.run()
    
    

async def generate_dataset(generator: DatasetGenerator, file_path):
    # 没有数据的时候，通过数据合成的方式来合成数据集
    train_set = await generator.generate(task_desc="你的主要职责是解决关于图数据库的各种问题，包括实体查询、多跳推理等等", dataset_name="test", size=10)
    print(f"end, train_set={train_set}")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([row.model_dump() for row in train_set.data], f, indent=2, ensure_ascii=False)
    return train_set
    
if __name__ == "__main__":
    asyncio.run(test())