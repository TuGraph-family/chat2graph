from dataclasses import dataclass
from typing import Optional

from app.agent.job import Job


@dataclass
class Task:
    """Task in the system.

    Attributes:
        job (Job): The job assigned to the experts.
        task_description (str): The description of the inference task for the reasoner.
        task_context (Optional[str]): The context of the inference task for the reasoner.
        output_schema (Optional[str]): The output schema of the inference task for the reasoner.
    """

    # TODO: make the job optional. Now the reasoner memory must use the session_id and job_id to store the memory.
    job: Job
    task_description: str
    task_context: Optional[str] = None
    output_schema: str = "Output schema is not determined."

    def get_session_id(self) -> str:
        """Get the unique identifier of the session."""
        return self.job.session_id

    def get_job_id(self) -> str:
        """Get the unique identifier of the job."""
        return self.job.id


class TaskDescriptor:
    """Task descriptor."""

    def aggregate(
        self,
        profile: str,
        instruction: str,
        output_schema: str,
        knowledge: str,
        env_info: str,
        action_rels: str,
        scratchpad: str,
        job: Job,
        operator_context_prompt_template: str,
    ) -> Task:
        """Format the task."""
        # it is defined by the operator config
        task_description = profile + "\n" + instruction

        # input data from the retrieved data, the scratchpad, the toolkit, the job context
        task_context = operator_context_prompt_template.format(
            context=job.context + "\n" + env_info,
            knowledge=knowledge,
            action_rels=action_rels,
            scratchpad=scratchpad,
        )

        return Task(
            task_description=task_description,
            task_context=task_context,
            output_schema=output_schema,
            job=job,
        )
