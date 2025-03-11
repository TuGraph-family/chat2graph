from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.job_do import JobDo
from app.core.model.job import Job, SubJob


class JobDao(Dao[JobDo]):
    """Job Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(JobDo, session)

    def save_job(self, job: Job) -> JobDo:
        """Create a new job model."""
        if isinstance(job, SubJob):
            return self.create(
                id=job.id,
                goal=job.goal,
                context=job.context,
                session_id=job.session_id,
                output_schema=job.output_schema,
                life_cycle=job.life_cycle,
            )
        return self.create(
            id=job.id,
            goal=job.goal,
            context=job.context,
            session_id=job.session_id,
            assigned_expert_name=job.assigned_expert_name,
        )

    def update_job(self, job: Job) -> JobDo:
        """Update a job model."""
        if isinstance(job, SubJob):
            return self.update(
                id=job.id,
                goal=job.goal,
                context=job.context,
                session_id=job.session_id,
                output_schema=job.output_schema,
                life_cycle=job.life_cycle,
            )
        return self.update(
            id=job.id,
            goal=job.goal,
            context=job.context,
            session_id=job.session_id,
            assigned_expert_name=job.assigned_expert_name,
        )

    def get_job_by_id(self, id: str) -> Job:
        """Get a job by ID."""
        result = self.get_by_id(id=id)
        if not result:
            raise ValueError(f"Job with ID {id} not found")
        if result.assigned_expert_name:
            return Job(
                goal=str(result.goal),
                context=str(result.context),
                id=str(result.id),
                session_id=str(result.session_id),
                assigned_expert_name=str(result.assigned_expert_name),
            )
        return SubJob(
            goal=str(result.goal),
            context=str(result.context),
            id=str(result.id),
            session_id=str(result.session_id),
            output_schema=str(result.output_schema),
            life_cycle=int(result.life_cycle),
        )

    def remove_job(self, id: str) -> None:
        """Remove a job by ID."""
        self.delete(id=id)
