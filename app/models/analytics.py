from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    device_id = Column(String(255), nullable=False)
    session_start = Column(DateTime(timezone=True), default=datetime.utcnow)
    session_end = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    app_version = Column(String(20))
    os_version = Column(String(20))
    actions_count = Column(Integer, default=0)
    jobs_viewed_count = Column(Integer, default=0)
    jobs_saved_count = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    actions = relationship("UserAction", back_populates="session", cascade="all, delete-orphan")
    searches = relationship("SearchAnalytics", back_populates="session", cascade="all, delete-orphan")
    job_engagements = relationship("JobEngagement", back_populates="session", cascade="all, delete-orphan")

class UserAction(Base):
    __tablename__ = "user_actions"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.user_sessions.id', ondelete='SET NULL'))
    action_type = Column(String(50), nullable=False)
    action_details = Column(JSONB, default=dict)
    job_id = Column(Integer, ForeignKey('scraper.jobs_jobpost.id', ondelete='SET NULL'))
    search_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.search_analytics.id', ondelete='SET NULL'))
    search_query = Column(String(500))
    page_url = Column(String(500))
    duration_seconds = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="actions")
    session = relationship("UserSession", back_populates="actions")
    # job = relationship("JobPost", back_populates="actions")  # Uncomment when JobPost model is available
    search = relationship("SearchAnalytics", back_populates="actions")

class SearchAnalytics(Base):
    __tablename__ = "search_analytics"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.user_sessions.id', ondelete='SET NULL'))
    search_query = Column(String(500), nullable=False)
    normalized_query = Column(String(500))
    results_count = Column(Integer, default=0)
    clicked_results = Column(Integer, default=0)
    time_to_first_click = Column(Integer)
    total_session_time = Column(Integer, default=0)
    filters_applied = Column(JSONB, default=dict)
    result_job_ids = Column(JSONB, default=list)
    clicked_job_ids = Column(JSONB, default=list)
    search_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="searches")
    session = relationship("UserSession", back_populates="searches")
    actions = relationship("UserAction", back_populates="search", cascade="all, delete-orphan")

class JobEngagement(Base):
    __tablename__ = "job_engagement"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(Integer, ForeignKey('scraper.jobs_jobpost.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.user_sessions.id', ondelete='SET NULL'))
    job_title = Column(String(500))
    job_company = Column(String(255))
    job_source = Column(String(100))
    job_location = Column(String(255))
    
    # Engagement metrics
    total_view_time = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    first_viewed_at = Column(DateTime(timezone=True))
    last_viewed_at = Column(DateTime(timezone=True))
    
    # User actions
    is_saved = Column(Boolean, default=False)
    saved_at = Column(DateTime(timezone=True))
    unsaved_at = Column(DateTime(timezone=True))
    
    # Application tracking
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True))
    application_source = Column(String(100))
    
    # Engagement scoring
    engagement_score = Column(Integer, default=0)
    last_calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="job_engagements")
    session = relationship("UserSession", back_populates="job_engagements")
    # job = relationship("JobPost", back_populates="engagements")  # Uncomment when JobPost model is available
    notifications = relationship("NotificationAnalytics", back_populates="job_engagement", cascade="all, delete-orphan")

class UserPreferencesHistory(Base):
    __tablename__ = "user_preferences_history"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    change_type = Column(String(50), nullable=False)
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    change_reason = Column(String(100))
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences_history")

class NotificationAnalytics(Base):
    __tablename__ = "notification_analytics"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    device_token_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id', ondelete='SET NULL'))
    notification_type = Column(String(50), nullable=False)
    notification_title = Column(String(200))
    notification_body = Column(Text)
    job_id = Column(Integer, ForeignKey('scraper.jobs_jobpost.id', ondelete='SET NULL'))
    job_engagement_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.job_engagement.id', ondelete='SET NULL'))
    
    # Delivery tracking
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    delivered_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    
    # Status tracking
    delivery_status = Column(String(20), default='sent')
    error_message = Column(Text)
    
    # Engagement tracking
    led_to_app_open = Column(Boolean, default=False)
    led_to_job_view = Column(Boolean, default=False)
    led_to_job_save = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    device_token = relationship("DeviceToken", back_populates="notifications")
    # job = relationship("JobPost", back_populates="notifications")  # Uncomment when JobPost model is available
    job_engagement = relationship("JobEngagement", back_populates="notifications")