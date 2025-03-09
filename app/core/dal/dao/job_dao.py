from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import DAO
from app.core.dal.model.job_model import JobModel
from app.core.model.job import Job, SubJob


class JobDAO(DAO[JobModel]):
    """Job Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(JobModel, session)

    def create_job(self, job: Job) -> JobModel:
        """Create a new job model."""
        if isinstance(job, SubJob):
            return self.create(
                goal=job.goal,
                context=job.context,
                id=job.id,
                session_id=job.session_id,
                output_schema=job.output_schema,
                life_cycle=job.life_cycle,
            )
        return self.create(
            goal=job.goal,
            context=job.context,
            id=job.id,
            session_id=job.session_id,
            assigned_expert_name=job.assigned_expert_name,
        )

    def update_job(self, job: Job) -> JobModel:
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
