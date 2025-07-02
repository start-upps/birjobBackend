from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = {'schema': 'iosapp'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    device_token = Column(String(500), nullable=False)
    device_info = Column(JSONB, default=dict)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())