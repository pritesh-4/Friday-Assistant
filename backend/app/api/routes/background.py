from fastapi import APIRouter, HTTPException

from app.schemas.background import Job, JobCreate, JobStatus, Notification, NotificationStatus
from app.services.job_service import job_service
from app.services.notification_service import notification_service

router = APIRouter(prefix="/background", tags=["background"])

@router.get("/jobs", response_model=list[Job])
async def list_jobs(status: JobStatus | None = None):
    return await job_service.list_jobs(status=status)

@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/jobs", response_model=Job, status_code=201)
async def create_job(job_data: JobCreate):
    return await job_service.enqueue_job(job_data)

@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str):
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    await job_service.update_status(job_id, JobStatus.RETRY)
    return {"status": "retrying"}

@router.get("/notifications", response_model=list[Notification])
async def list_notifications(status: NotificationStatus | None = None):
    return await notification_service.list_notifications(status=status)

@router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    await notification_service.mark_as_read(notif_id)
    return {"status": "read"}
