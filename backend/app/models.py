from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, nullable=False)
    show_name = Column(String, nullable=False)
    episode = Column(Integer, nullable=False)
    state = Column(String, default="queued")
    error_msg = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tasks = relationship("Task", back_populates="job", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    name = Column(String, nullable=False)
    state = Column(String, default="pending")
    try_count = Column(Integer, default=0)
    logs = Column(Text, default="")
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    job = relationship("Job", back_populates="tasks")


class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    type = Column(String, nullable=False)
    path = Column(String, nullable=False)
    size = Column(Integer, default=0)
    meta = Column(JSON, default={})
    job = relationship("Job", back_populates="artifacts")
