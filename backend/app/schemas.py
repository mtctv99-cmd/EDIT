from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class Artifact(BaseModel):
    id: int
    type: str
    path: str
    size: int

    class Config:
        orm_mode = True


class Task(BaseModel):
    id: int
    name: str
    state: str
    logs: str

    class Config:
        orm_mode = True


class JobCreate(BaseModel):
    source_url: str
    show_name: str
    episode: int


class Job(BaseModel):
    id: int
    source_url: str
    show_name: str
    episode: int
    state: str
    created_at: datetime
    updated_at: datetime
    tasks: List[Task] = []
    artifacts: List[Artifact] = []

    class Config:
        orm_mode = True
