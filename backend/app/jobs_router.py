from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import schemas, models
from .deps import get_db
from .queue import queue
from .workers.pipeline import run_pipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=schemas.Job)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    job = models.Job(source_url=payload.source_url, show_name=payload.show_name, episode=payload.episode)
    db.add(job)
    db.commit()
    db.refresh(job)
    queue.enqueue(run_pipeline, job.id)
    return job


@router.get("/{job_id}", response_model=schemas.Job)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
