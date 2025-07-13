import re

from inspect_ai import eval
from inspect_ai.model import get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_evals.gaia import gaia

from chat2graph_model import Chat2GraphModel  # noqa


@solver
def chat2graph_solver() -> Solver:
    """A simple solver that calls the model once and uses the response as the answer."""

    def _replace_shared_file_path(content: str) -> str:
        # Replace any /shared_files/xxx with ./shared_files/xxx
        return re.sub(r"/shared_files/([\w\-\.]+)", r"./shared_files/\1", content)

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        # Replace file paths in all message contents
        for msg in state.messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                msg.content = _replace_shared_file_path(msg.content)
        state.output = await get_model().generate(state.messages)
        # The content of the response is the final answer.
        state.output.completion = state.output.message.content
        return state

    return solve


def main():
    """Main function to run the GAIA benchmark with the custom Chat2GraphModel."""
    task = gaia(
        subset="2023_level2",
        split="validation",
        solver=chat2graph_solver(),
        instance_ids=["32102e3e-d12a-4209-9163-7b3a104efe5d"],
    )


    eval(
        task,
        model="chat2graph/chat2graph",
        # limit=1,  # Run only N tasks for a quick test
        timeout=600,
    )


if __name__ == "__main__":
    main()
