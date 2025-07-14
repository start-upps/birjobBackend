"""
Analytics service for tracking user actions
Simple wrapper around database operations for user_analytics table
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.database import db_manager
from app.services.privacy_analytics_service import privacy_analytics_service

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for tracking user analytics and actions"""
    
    async def track_action(self, device_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track a user action in the analytics table (PRIVACY-COMPLIANT)
        Only tracks if user has consented to analytics
        
        Args:
            device_id: UUID of the device user
            action: Action type (e.g., 'profile_view', 'preferences_update')
            metadata: Optional metadata dict
            
        Returns:
            bool: True if successfully tracked (or skipped due to no consent), False if error
        """
        # Use privacy-compliant service that checks consent first
        return await privacy_analytics_service.track_action_with_consent(device_id, action, metadata)
    
    async def get_device_analytics(self, device_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics summary for a device (PRIVACY-COMPLIANT)
        Only returns data if user has consented to analytics
        
        Args:
            device_id: UUID of the device user
            days: Number of days to look back
            
        Returns:
            Dict with analytics summary or consent message
        """
        # Use privacy-compliant service that checks consent first
        has_consent, analytics_data = await privacy_analytics_service.get_user_analytics_with_consent(device_id)
        return analytics_data
    
    async def get_action_count(self, device_id: str, action: str, days: int = 30) -> int:
        """
        Get count of specific action for a device
        
        Args:
            device_id: UUID of the device user
            action: Action to count
            days: Number of days to look back
            
        Returns:
            int: Count of actions
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM iosapp.user_analytics
                WHERE device_id = $1 AND action = $2 
                AND created_at >= NOW() - INTERVAL '%s days'
            """ % days
            
            result = await db_manager.execute_query(query, device_id, action)
            return result[0]['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to get action count for {action}: {e}")
            return 0

# Global instance
analytics_service = AnalyticsService()