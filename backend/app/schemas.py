from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Artifact(BaseModel):
    id: int
    type: str
    path: str
    size: int

    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    id: int
    name: str
    state: str
    logs: str

    model_config = ConfigDict(from_attributes=True)


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
    tasks: List[Task] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
