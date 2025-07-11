from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class JobNotificationHistory(Base):
    __tablename__ = "job_notification_history"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    job_unique_key = Column(String(255), nullable=False)
    job_id = Column(Integer, nullable=False)
    job_title = Column(String(500), nullable=False)
    job_company = Column(String(255), nullable=False)
    job_source = Column(String(100))
    matched_keywords = Column(JSONB, default=list)
    notification_sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_history")
    push_notifications = relationship("PushNotification", back_populates="notification_history")

class PushNotification(Base):
    __tablename__ = "push_notifications" 
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.job_notification_history.id', ondelete='SET NULL'))
    notification_type = Column(String(50), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    apns_response = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add check constraints
    __table_args__ = (
        CheckConstraint("notification_type IN ('job_match', 'daily_digest', 'system')", name='check_notification_type'),
        CheckConstraint("status IN ('pending', 'sent', 'failed', 'cancelled')", name='check_status'),
        {'schema': 'iosapp'}
    )
    
    # Relationships
    user = relationship("User")
    device_token = relationship("DeviceToken")
    notification_history = relationship("JobNotificationHistory", back_populates="push_notifications")

class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id', ondelete='CASCADE'), nullable=False)
    
    # Notification preferences
    job_matches_enabled = Column(Boolean, default=True)
    daily_digest_enabled = Column(Boolean, default=True)
    system_notifications_enabled = Column(Boolean, default=True)
    
    # Timing preferences
    quiet_hours_start = Column(Integer, default=22)
    quiet_hours_end = Column(Integer, default=8)
    timezone = Column(String(50), default='UTC')
    
    # Frequency limits
    max_notifications_per_hour = Column(Integer, default=5)
    max_notifications_per_day = Column(Integer, default=20)
    
    # Keywords
    keywords = Column(JSONB, default=list)
    keyword_match_mode = Column(String(20), default='any')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add check constraints
    __table_args__ = (
        CheckConstraint("quiet_hours_start >= 0 AND quiet_hours_start <= 23", name='check_quiet_hours_start'),
        CheckConstraint("quiet_hours_end >= 0 AND quiet_hours_end <= 23", name='check_quiet_hours_end'),
        CheckConstraint("keyword_match_mode IN ('any', 'all')", name='check_keyword_match_mode'),
        {'schema': 'iosapp'}
    )
    
    # Relationships
    user = relationship("User")
    device_token = relationship("DeviceToken")

class NotificationDeliveryLog(Base):
    __tablename__ = "notification_delivery_log"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.push_notifications.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.users.id', ondelete='CASCADE'), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey('iosapp.device_tokens.id', ondelete='CASCADE'), nullable=False)
    
    # Delivery details
    attempt_number = Column(Integer, nullable=False, default=1)
    delivery_status = Column(String(20), nullable=False)
    error_message = Column(Text)
    apns_message_id = Column(String(255))
    apns_timestamp = Column(DateTime)
    
    # Performance metrics
    processing_time_ms = Column(Integer)
    queue_time_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add check constraint
    __table_args__ = (
        CheckConstraint("delivery_status IN ('success', 'failed', 'throttled', 'quiet_hours', 'device_inactive')", name='check_delivery_status'),
        {'schema': 'iosapp'}
    )
    
    # Relationships
    notification = relationship("PushNotification")
    user = relationship("User")
    device_token = relationship("DeviceToken")