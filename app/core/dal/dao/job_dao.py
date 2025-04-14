from typing import Optional, cast

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.job_do import JobDo
from app.core.model.job import Job, JobType, SubJob
from app.core.model.job_result import JobResult


class JobDao(Dao[JobDo]):
    """Job Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(JobDo, session)

    def save_job(self, job: Job) -> JobDo:
        """Create a new job model."""
        try:
            self.get_job_by_id(id=job.id)
            return self._update_job(job=job)
        except ValueError:
            if isinstance(job, SubJob):
                return self.create(
                    category=JobType.SUB_JOB.value,
                    id=job.id,
                    goal=job.goal,
                    context=job.context,
                    session_id=job.session_id,
                    original_job_id=job.original_job_id,
                    expert_id=job.expert_id,
                    output_schema=job.output_schema,
                    life_cycle=job.life_cycle,
                    is_legacy=job.is_legacy,
                    thinking=job.thinking,
                    assigned_expert_name=job.assigned_expert_name,
                )
            return self.create(
                category=JobType.JOB.value,
                id=job.id,
                goal=job.goal,
                context=job.context,
                session_id=job.session_id,
                assigned_expert_name=job.assigned_expert_name,
            )

    def _update_job(self, job: Job) -> JobDo:
        """Update a job model."""
        if isinstance(job, SubJob):
            return self.update(
                id=job.id,
                goal=job.goal,
                context=job.context,
                session_id=job.session_id,
                original_job_id=job.original_job_id,
                expert_id=job.expert_id,
                output_schema=job.output_schema,
                life_cycle=job.life_cycle,
                is_legacy=job.is_legacy,
                thinking=job.thinking,
                assigned_expert_name=job.assigned_expert_name,
            )
        return self.update(
            id=job.id,
            goal=job.goal,
            context=job.context,
            session_id=job.session_id,
            assigned_expert_name=job.assigned_expert_name,
            dag=job.dag,
        )

    def save_job_result(self, job_result: JobResult) -> JobDo:
        """Update a job model with the job result."""
        return self.update(
            id=job_result.job_id,
            status=job_result.status.value,
            duration=job_result.duration,
            tokens=job_result.tokens,
        )

    def get_job_by_id(self, id: str) -> Job:
        """Get a job by ID."""
        result = self.get_by_id(id=id)
        if not result:
            raise ValueError(f"Job with ID {id} not found")
        if result.category == JobType.JOB.value:
            return Job(
                id=cast(str, result.id),
                goal=cast(str, result.goal),
                context=cast(str, result.context),
                session_id=cast(str, result.session_id),
                assigned_expert_name=cast(Optional[str], result.assigned_expert_name),
                dag=cast(Optional[str], result.dag),
            )
        return SubJob(
            id=cast(str, result.id),
            goal=cast(str, result.goal),
            context=cast(str, result.context),
            session_id=cast(str, result.session_id),
            original_job_id=cast(str, result.original_job_id),
            expert_id=cast(str, result.expert_id),
            output_schema=cast(str, result.output_schema),
            life_cycle=cast(int, result.life_cycle),
            is_legacy=cast(bool, result.is_legacy),
            thinking=cast(
                Optional[str],
                str(result.thinking) if result.thinking else None,
            ),
            assigned_expert_name=cast(
                Optional[str],
                str(result.assigned_expert_name) if result.assigned_expert_name else None,
            ),
        )
