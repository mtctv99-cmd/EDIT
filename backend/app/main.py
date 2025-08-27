from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .models import Base
from .deps import engine
from .jobs_router import router as jobs_router
from .views import router as views_router

app = FastAPI(title="EDIT")
app.include_router(jobs_router)
app.include_router(views_router)
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
