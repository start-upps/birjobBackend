from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'iosapp'}
    
    # Basic identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String(255), index=True)  # Optional email for notifications
    
    # Simple job preferences
    keywords = Column(JSON, default=list)  # Job search keywords
    preferred_sources = Column(JSON, default=list)  # Preferred job sources
    
    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    last_notified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobView(Base):
    __tablename__ = "job_views"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(Integer, nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)