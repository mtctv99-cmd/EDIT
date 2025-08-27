from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .deps import get_db
from . import models

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="backend/app/templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})


@router.get("/jobs/{job_id}/panel", response_class=HTMLResponse)
def job_panel(job_id: int, request: Request, db: Session = Depends(get_db)):
    job = db.query(models.Job).get(job_id)
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})
