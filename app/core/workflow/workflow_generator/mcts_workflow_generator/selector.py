from abc import abstractmethod
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import OptimizeResp, WorkflowLogFormat
from app.core.prompt.workflow_generator import optimize_prompt_template
import numpy as np


class Selector:
    @abstractmethod
    def select(self, sample_size: int, logs: dict[int, WorkflowLogFormat]) -> WorkflowLogFormat:
        ...

class MixedProbabilitySelector(Selector):
    def select(self, sample_size: int, logs: dict[int, WorkflowLogFormat]) -> WorkflowLogFormat:
        # 获取sample个top的score的workflow，包含初始workflow
        list_items = [log_format for _, log_format in logs.items()]
        top_items: list[WorkflowLogFormat] = []
        list_items.sort(key= lambda x: x.score, reverse=True)
        top_items.extend(list_items[:sample_size - 1])
        has_round1 = False
        for item in top_items:
            if item.round_number == 1:
                has_round1 = True
                break
        
        if not has_round1:
            top_items.append(logs[1])

        elif sample_size <= len(list_items):
            top_items.append(list_items[sample_size - 1])

        # 计算概率分布
        scores = [item.score * 100 for item in top_items]
        probabilities = self._compute_probabilities(scores)
        index = np.random.choice(len(top_items), p=probabilities)
        return top_items[index]

    def _compute_probabilities(self, scores: list[float], alpha=0.2, lambda_=0.3):
        scores = np.array(scores, dtype=np.float64)
        n = len(scores)

        if n == 0:
            raise ValueError("Score list is empty.")

        uniform_prob = np.full(n, 1.0 / n, dtype=np.float64)

        max_score = np.max(scores)
        shifted_scores = scores - max_score
        exp_weights = np.exp(alpha * shifted_scores)

        sum_exp_weights = np.sum(exp_weights)
        if sum_exp_weights == 0:
            raise ValueError("Sum of exponential weights is 0, cannot normalize.")

        score_prob = exp_weights / sum_exp_weights

        mixed_prob = lambda_ * uniform_prob + (1 - lambda_) * score_prob

        total_prob = np.sum(mixed_prob)
        if not np.isclose(total_prob, 1.0):
            mixed_prob = mixed_prob / total_prob

        return mixed_prob