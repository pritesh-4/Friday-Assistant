"""Service for managing background jobs."""

import json

from app.core.logging import get_logger
from app.db.database import database
from app.schemas.background import Job, JobCreate, JobStatus
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger(__name__)

class JobService:
    async def enqueue_job(self, data: JobCreate) -> Job:
        job_id = generate_uuid()
        now = get_utc_now()
        
        scheduled_at = data.scheduled_at or now
        status = JobStatus.SCHEDULED if scheduled_at > now else JobStatus.QUEUED
        
        await database.execute(
            """
            INSERT INTO background_jobs (id, task_type, payload, status, scheduled_at, max_retries, agent_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id, data.task_type, json.dumps(data.payload), status.value, 
                scheduled_at.isoformat(), data.max_retries, data.agent_name, 
                now.isoformat(), now.isoformat()
            )
        )
        logger.info(f"Enqueued job {job_id} of type {data.task_type}")
        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> Job | None:
        row = await database.fetch_one("SELECT * FROM background_jobs WHERE id = ?", (job_id,))
        if not row:
            return None
        
        job_dict = dict(row)
        job_dict["payload"] = json.loads(job_dict["payload"])
        return Job.model_validate(job_dict)

    async def list_jobs(self, status: JobStatus | None = None, limit: int = 50) -> list[Job]:
        if status:
            rows = await database.fetch_all(
                "SELECT * FROM background_jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status.value, limit)
            )
        else:
            rows = await database.fetch_all(
                "SELECT * FROM background_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            
        jobs = []
        for r in rows:
            job_dict = dict(r)
            job_dict["payload"] = json.loads(job_dict["payload"])
            jobs.append(Job.model_validate(job_dict))
        return jobs

    async def update_status(self, job_id: str, status: JobStatus, error_message: str | None = None) -> None:
        now = get_utc_now().isoformat()
        updates = ["status = ?", "updated_at = ?"]
        params = [status.value, now]
        
        if status == JobStatus.RUNNING:
            updates.append("started_at = ?")
            params.append(now)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
            updates.append("completed_at = ?")
            params.append(now)
            
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
            
        params.append(job_id)
        query = f"UPDATE background_jobs SET {', '.join(updates)} WHERE id = ?"
        
        await database.execute(query, tuple(params))

    async def increment_retry(self, job_id: str) -> None:
        now = get_utc_now().isoformat()
        await database.execute(
            "UPDATE background_jobs SET retries = retries + 1, updated_at = ? WHERE id = ?",
            (now, job_id)
        )

# Global singleton
job_service = JobService()
