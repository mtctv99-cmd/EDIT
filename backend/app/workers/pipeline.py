import logging
from sqlalchemy.orm import Session
from datetime import datetime

from ..deps import SessionLocal
from .. import models
from . import steps_download, steps_speed, steps_cut, steps_asr, steps_translate, steps_render, steps_report

logger = logging.getLogger(__name__)


STEPS = [
    ("download", steps_download.run),
    ("speed", steps_speed.run),
    ("cut", steps_cut.run),
    ("asr", steps_asr.run),
    ("translate", steps_translate.run),
    ("render", steps_render.run),
    ("report", steps_report.run),
]


def run_pipeline(job_id: int):
    db: Session = SessionLocal()
    job = db.query(models.Job).get(job_id)
    if not job:
        logger.error("Job %s not found", job_id)
        return
    job.state = "running"
    db.commit()
    try:
        for name, fn in STEPS:
            task = models.Task(job_id=job_id, name=name, state="running", started_at=datetime.utcnow())
            db.add(task)
            db.commit()
            try:
                fn(job, db)
                task.state = "done"
            except Exception as exc:  # noqa: BLE001
                task.state = "failed"
                task.logs = str(exc)
                job.state = "failed"
                db.commit()
                raise
            finally:
                task.finished_at = datetime.utcnow()
                db.commit()
        job.state = "done"
        db.commit()
    finally:
        db.close()
