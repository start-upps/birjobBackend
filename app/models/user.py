from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    location = Column(String(255))
    current_job_title = Column(String(255))
    years_of_experience = Column(Integer)
    linkedin_profile = Column(String(500))
    portfolio_url = Column(String(500))
    bio = Column(Text)
    
    # Job Preferences (stored as JSON)
    desired_job_types = Column(JSON)  # ["Full-time", "Contract"]
    remote_work_preference = Column(String(50))  # "Remote", "Hybrid", "On-site"
    skills = Column(JSON)  # ["Swift", "SwiftUI", "UIKit"]
    preferred_locations = Column(JSON)  # ["San Francisco", "Remote"]
    min_salary = Column(Integer)
    max_salary = Column(Integer)
    salary_currency = Column(String(10), default="USD")
    salary_negotiable = Column(Boolean, default=True)
    
    # Notification Settings
    job_matches_enabled = Column(Boolean, default=True)
    application_reminders_enabled = Column(Boolean, default=True)
    weekly_digest_enabled = Column(Boolean, default=False)
    market_insights_enabled = Column(Boolean, default=True)
    quiet_hours_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="08:00")
    preferred_notification_time = Column(String(5), default="09:00")
    
    # Privacy Settings
    profile_visibility = Column(String(20), default="Public")  # "Public", "Private"
    share_analytics = Column(Boolean, default=True)
    share_job_view_history = Column(Boolean, default=False)
    allow_personalized_recommendations = Column(Boolean, default=True)
    
    # Profile Metadata
    profile_completeness = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")
    job_views = relationship("JobView", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id'), nullable=False)
    job_id = Column(Integer, nullable=False)
    notes = Column(Text)
    application_status = Column(String(20), default="not_applied")  # "not_applied", "applied", "interviewing", "rejected", "offered"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_jobs")


class JobView(Base):
    __tablename__ = "job_views"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id'), nullable=False)
    job_id = Column(Integer, nullable=False)
    view_duration = Column(Integer)  # seconds
    source = Column(String(50))  # "job_list", "recommendations", "search"
    viewed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="job_views")


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id'), nullable=False)
    job_id = Column(Integer, nullable=False)
    
    # Application details
    status = Column(String(20), default="pending")  # "pending", "interview", "rejected", "offer"
    applied_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    follow_up_date = Column(DateTime)
    
    # Application source/method
    application_source = Column(String(100))  # "company_website", "linkedin", "indeed", etc.
    
    # Relationships
    user = relationship("User", back_populates="applications")


class UserAnalytics(Base):
    __tablename__ = "user_analytics"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id'), nullable=False)
    
    # Profile insights
    profile_strength = Column(Integer, default=0)
    market_fit = Column(Integer, default=0)
    
    # Job activity stats
    total_jobs_viewed = Column(Integer, default=0)
    total_jobs_saved = Column(Integer, default=0)
    total_applications = Column(Integer, default=0)
    average_view_time = Column(DECIMAL(10, 2), default=0)
    
    # Matching insights
    total_matches = Column(Integer, default=0)
    average_match_score = Column(DECIMAL(5, 2), default=0)
    
    # Computed insights (stored as JSON)
    improvement_areas = Column(JSON)
    most_viewed_categories = Column(JSON)
    top_matching_companies = Column(JSON)
    recommended_skills = Column(JSON)
    market_insights = Column(JSON)
    
    # Timestamps
    computed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)