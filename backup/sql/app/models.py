from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .db import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # Passwords are no longer stored in the SQL database. Authentication
    # is handled by AWS Cognito User Pools. Keep an optional `cognito_sub`
    # column to associate a local profile with a Cognito user if desired.
    cognito_sub = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Voice(Base):
    __tablename__ = "voices"
    id = Column(Integer, primary_key=True, index=True)
    engine = Column(String, index=True)
    language = Column(String, index=True)
    display_name = Column(String)
    model_path = Column(String)
    supports_alignments = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    language = Column(String)
    voice_id = Column(String)
    text = Column(Text, nullable=True)
    include_alignments = Column(Boolean, default=False)
    original_filename = Column(String, nullable=True)
    total_chunks = Column(Integer, default=0)
    completed_chunks = Column(Integer, default=0)
    status = Column(String, default="queued")
    s3_final_url = Column(String, nullable=True)
    alignments_s3_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    index = Column(Integer)
    text_excerpt = Column(Text)
    s3_temp_path = Column(String, nullable=True)
    alignments_json = Column(Text, nullable=True)
    status = Column(String, default="pending")
    duration_seconds = Column(Integer, default=0)
    attempts = Column(Integer, default=0)

    job = relationship("Job")
