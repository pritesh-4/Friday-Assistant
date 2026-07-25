"""Background Async Worker for executing queued jobs."""

import asyncio

from app.core.logging import get_logger
from app.db.database import database
from app.schemas.background import JobStatus, NotificationCreate, NotificationType
from app.services.job_service import job_service
from app.services.notification_service import notification_service
from app.agents.agent_manager import AgentManager
from app.tools.executor import PermissionRequiredError
from app.utils.helpers import get_utc_now

logger = get_logger(__name__)

class BackgroundWorker:
    def __init__(self, agent_manager: AgentManager, poll_interval: int = 5):
        self.agent_manager = agent_manager
        self.poll_interval = poll_interval
        self._running = False

    async def start(self):
        """Starts the worker polling loop."""
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._loop())
        logger.info(f"BackgroundWorker started (polling every {self.poll_interval}s).")

    def stop(self):
        self._running = False
        logger.info("BackgroundWorker stopped.")

    async def _loop(self):
        while self._running:
            try:
                await self._process_ready_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
            finally:
                if self._running:
                    await asyncio.sleep(self.poll_interval)

    async def _process_ready_jobs(self):
        now = get_utc_now().isoformat()
        
        # Atomically find and lock ONE job to prevent parallel execution conflicts in this MVP
        # We process 'queued' or 'retry', OR 'scheduled' where time has passed
        query = """
            SELECT id FROM background_jobs 
            WHERE (status IN (?, ?))
               OR (status = ? AND scheduled_at <= ?)
            ORDER BY created_at ASC 
            LIMIT 1
        """
        params = (JobStatus.QUEUED.value, JobStatus.RETRY.value, JobStatus.SCHEDULED.value, now)
        
        row = await database.fetch_one(query, params)
        if not row:
            return # No jobs ready
            
        job_id = row["id"]
        job = await job_service.get_job(job_id)
        if not job:
            return
            
        # Transition to RUNNING
        await job_service.update_status(job_id, JobStatus.RUNNING)
        logger.info(f"Worker picked up job {job_id} ({job.task_type})")
        
        try:
            # Route to appropriate logic based on task_type
            if job.task_type == "agent_execution":
                await self._execute_agent_task(job)
            else:
                # Placeholder for direct tasks (e.g., kb_index)
                await asyncio.sleep(2) # Simulating work
                logger.info(f"Completed built-in task {job.task_type}")
                
            await job_service.update_status(job_id, JobStatus.COMPLETED)
            
            # Send Notification
            await notification_service.create_notification(NotificationCreate(
                title=f"Task Completed: {job.task_type}",
                message=f"Background job {job_id} finished successfully.",
                type=NotificationType.SUCCESS
            ))
            
        except PermissionRequiredError as e:
            logger.warning(f"Job {job_id} blocked by permission barrier: {e}")
            await job_service.update_status(job_id, JobStatus.WAITING, error_message=str(e))
            
            await notification_service.create_notification(NotificationCreate(
                title="Action Required",
                message=f"Background job '{job.task_type}' requires your permission to proceed.",
                type=NotificationType.APPROVAL,
                action_url=f"/background?job={job_id}"
            ))
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            if job.retries < job.max_retries:
                # Apply exponential backoff? For MVP we just queue it for next loop
                await job_service.increment_retry(job_id)
                await job_service.update_status(job_id, JobStatus.RETRY, error_message=str(e))
            else:
                await job_service.update_status(job_id, JobStatus.FAILED, error_message=str(e))
                await notification_service.create_notification(NotificationCreate(
                    title=f"Task Failed: {job.task_type}",
                    message=f"Job failed permanently after {job.max_retries} retries. Error: {e}",
                    type=NotificationType.ERROR
                ))

    async def _execute_agent_task(self, job):
        agent_name = job.agent_name or "WebResearchAgent"
        agent = self.agent_manager.spawn_agent(agent_name)
        
        prompt = job.payload.get("prompt", "")
        # For simplicity, we just execute and drop the result in memory/db. 
        # Real system would pipe `final_content` somewhere meaningful based on payload.
        final_content = ""
        async for chunk in agent.execute(prompt, [], approved_permissions=[]):
            final_content += chunk + "\\n"
        
        # Optionally save to memory
        # await memory_service.create_memory(...)
