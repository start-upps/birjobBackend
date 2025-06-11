from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import uuid
import logging

from app.core.database import get_db
from app.models.device import DeviceToken, KeywordSubscription
from app.schemas.device import (
    KeywordSubscriptionRequest, 
    KeywordSubscriptionResponse,
    KeywordSubscriptionsResponse,
    KeywordSubscriptionInfo,
    APIResponse
)
from app.core.redis_client import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=KeywordSubscriptionResponse)
async def create_keyword_subscription(
    request: KeywordSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Subscribe a device to keyword-based job notifications"""
    try:
        device_uuid = uuid.UUID(request.device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )
    
    try:
        # Verify device exists and is active
        stmt = select(DeviceToken).where(
            and_(DeviceToken.id == device_uuid, DeviceToken.is_active == True)
        )
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found or inactive"
            )
        
        # Create subscription
        subscription = KeywordSubscription(
            device_id=device_uuid,
            keywords=request.keywords,
            sources=request.sources,
            location_filters=request.location_filters.model_dump() if request.location_filters else None
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        # Clear cached keywords for this device
        await redis_client.delete(f"device_keywords:{request.device_id}")
        
        logger.info(f"Keyword subscription created: {subscription.id} for device {request.device_id}")
        
        return KeywordSubscriptionResponse(
            data={
                "subscription_id": str(subscription.id),
                "keywords_count": len(request.keywords),
                "sources_count": len(request.sources) if request.sources else 0,
                "created_at": subscription.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating keyword subscription: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create keyword subscription"
        )

@router.get("/{device_id}", response_model=KeywordSubscriptionsResponse)
async def get_keyword_subscriptions(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve current keyword subscriptions for a device"""
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )
    
    try:
        # Get all active subscriptions for device
        stmt = select(KeywordSubscription).where(
            and_(
                KeywordSubscription.device_id == device_uuid,
                KeywordSubscription.is_active == True
            )
        ).order_by(KeywordSubscription.created_at.desc())
        
        result = await db.execute(stmt)
        subscriptions = result.scalars().all()
        
        subscription_data = []
        for sub in subscriptions:
            subscription_data.append(KeywordSubscriptionInfo(
                subscription_id=str(sub.id),
                keywords=sub.keywords,
                sources=sub.sources,
                location_filters=sub.location_filters,
                created_at=sub.created_at,
                last_match=None  # TODO: Add query for last match timestamp
            ))
        
        return KeywordSubscriptionsResponse(
            data={"subscriptions": subscription_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting keyword subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get keyword subscriptions"
        )

@router.put("/{subscription_id}", response_model=KeywordSubscriptionResponse)
async def update_keyword_subscription(
    subscription_id: str,
    request: KeywordSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update keyword subscription settings"""
    try:
        subscription_uuid = uuid.UUID(subscription_id)
        device_uuid = uuid.UUID(request.device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    try:
        # Find subscription
        stmt = select(KeywordSubscription).where(
            and_(
                KeywordSubscription.id == subscription_uuid,
                KeywordSubscription.device_id == device_uuid,
                KeywordSubscription.is_active == True
            )
        )
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        # Update subscription
        subscription.keywords = request.keywords
        subscription.sources = request.sources
        subscription.location_filters = request.location_filters.model_dump() if request.location_filters else None
        
        await db.commit()
        await db.refresh(subscription)
        
        # Clear cached keywords
        await redis_client.delete(f"device_keywords:{request.device_id}")
        
        logger.info(f"Keyword subscription updated: {subscription_id}")
        
        return KeywordSubscriptionResponse(
            data={
                "subscription_id": str(subscription.id),
                "keywords_count": len(request.keywords),
                "sources_count": len(request.sources) if request.sources else 0,
                "updated_at": subscription.updated_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating keyword subscription: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update keyword subscription"
        )

@router.delete("/{subscription_id}", response_model=APIResponse)
async def delete_keyword_subscription(
    subscription_id: str,
    device_id: str,  # Query parameter to verify ownership
    db: AsyncSession = Depends(get_db)
):
    """Remove a keyword subscription"""
    try:
        subscription_uuid = uuid.UUID(subscription_id)
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    try:
        # Find and deactivate subscription
        stmt = select(KeywordSubscription).where(
            and_(
                KeywordSubscription.id == subscription_uuid,
                KeywordSubscription.device_id == device_uuid,
                KeywordSubscription.is_active == True
            )
        )
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        subscription.is_active = False
        await db.commit()
        
        # Clear cached keywords
        await redis_client.delete(f"device_keywords:{device_id}")
        
        logger.info(f"Keyword subscription deleted: {subscription_id}")
        
        return APIResponse(message="Keyword subscription removed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting keyword subscription: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete keyword subscription"
        )