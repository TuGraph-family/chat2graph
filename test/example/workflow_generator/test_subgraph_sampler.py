from typing import List, Type

from app.core.workflow.dataset_synthesis.sampler import (
    RandomSubgraphSampler,
    RandomWalkSampler,
    # SimpleRandomSubGraphSampler,
    SubGraphSampler,
)
from test.example.workflow_generator.utils import register_and_get_graph_db


def test():
    test_samplers: List[Type[SubGraphSampler]] = [
        # SimpleRandomSubGraphSampler,
        # EnhancedSubgraphSampler,
        # RandomWalkSampler,
        RandomSubgraphSampler,
    ]

    db = register_and_get_graph_db()
    for samplerCls in test_samplers:
        print(f"start test sampler={samplerCls.__name__}")
        try:
            sampler = samplerCls()
            for _ in range(3):
                subgraph = sampler.get_random_subgraph(graph_db=db, max_depth=2, max_nodes=5, max_edges=5)
                print(subgraph)
        except Exception as e:
            print(f"failed while testing sampler={samplerCls.__name__}, reason={e}")
            
            
if __name__ == "__main__":
    test()