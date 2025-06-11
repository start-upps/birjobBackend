from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_token = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(JSONB)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subscriptions = relationship("KeywordSubscription", back_populates="device", cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="device", cascade="all, delete-orphan")
    notifications = relationship("PushNotification", back_populates="device", cascade="all, delete-orphan")

class KeywordSubscription(Base):
    __tablename__ = "keyword_subscriptions"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id'), nullable=False, index=True)
    keywords = Column(ARRAY(Text), nullable=False)
    sources = Column(ARRAY(Text))
    location_filters = Column(JSONB)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Foreign key constraint handled at database level
    # Relationships
    device = relationship("DeviceToken", back_populates="subscriptions")

class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id'), nullable=False, index=True)
    job_id = Column(String, nullable=False)  # References scraper.jobs_jobpost.id
    matched_keywords = Column(ARRAY(Text), nullable=False)
    relevance_score = Column(String)  # DECIMAL(3,2) as string for easier handling
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    device = relationship("DeviceToken", back_populates="matches")
    notifications = relationship("PushNotification", back_populates="match")

class PushNotification(Base):
    __tablename__ = "push_notifications"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id'), nullable=False, index=True)
    match_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.job_matches.id'), nullable=True)
    notification_type = Column(String(50), nullable=False)  # 'job_match', 'daily_digest', 'system'
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), default='pending', index=True)  # 'pending', 'sent', 'delivered', 'failed'
    apns_response = Column(JSONB)
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    device = relationship("DeviceToken", back_populates="notifications")
    match = relationship("JobMatch", back_populates="notifications")

class ProcessedJob(Base):
    __tablename__ = "processed_jobs"
    __table_args__ = {'schema': 'iosapp'}
    
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id'), primary_key=True)
    job_id = Column(String, primary_key=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())