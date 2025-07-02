from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'iosapp'}
    
    # Basic identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True)  # Email is now unique
    
    # Simple job preferences
    keywords = Column(JSONB, default=list)  # Job search keywords
    preferred_sources = Column(JSONB, default=list)  # Preferred job sources
    
    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    last_notified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with proper foreign keys
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")
    job_views = relationship("JobView", back_populates="user", cascade="all, delete-orphan")
    
    # Analytics relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    actions = relationship("UserAction", back_populates="user", cascade="all, delete-orphan")
    searches = relationship("SearchAnalytics", back_populates="user", cascade="all, delete-orphan")
    job_engagements = relationship("JobEngagement", back_populates="user", cascade="all, delete-orphan")
    preferences_history = relationship("UserPreferencesHistory", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationAnalytics", back_populates="user", cascade="all, delete-orphan")


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(Integer, nullable=False)
    job_title = Column(String(500))  # Cache job title for performance
    job_company = Column(String(255))  # Cache job company for performance
    job_source = Column(String(100))  # Cache job source for performance
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to user
    user = relationship("User", back_populates="saved_jobs")


class JobView(Base):
    __tablename__ = "job_views"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(Integer, nullable=False)
    job_title = Column(String(500))  # Cache job title for analytics
    job_company = Column(String(255))  # Cache job company for analytics
    job_source = Column(String(100))  # Cache job source for analytics
    view_duration_seconds = Column(Integer, default=0)  # How long user viewed job
    viewed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to user
    user = relationship("User", back_populates="job_views")