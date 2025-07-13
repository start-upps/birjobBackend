"""
Analytics service for tracking user actions
Simple wrapper around database operations for user_analytics table
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.database import db_manager

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for tracking user analytics and actions"""
    
    async def track_action(self, device_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track a user action in the analytics table
        
        Args:
            device_id: UUID of the device user
            action: Action type (e.g., 'profile_view', 'preferences_update')
            metadata: Optional metadata dict
            
        Returns:
            bool: True if successfully tracked, False otherwise
        """
        try:
            metadata_json = json.dumps(metadata or {})
            
            query = """
                INSERT INTO iosapp.user_analytics (device_id, action, metadata, created_at)
                VALUES ($1, $2, $3, NOW())
            """
            
            await db_manager.execute_command(query, device_id, action, metadata_json)
            return True
            
        except Exception as e:
            logger.error(f"Failed to track action {action} for device {device_id}: {e}")
            return False
    
    async def get_device_analytics(self, device_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics summary for a device
        
        Args:
            device_id: UUID of the device user
            days: Number of days to look back
            
        Returns:
            Dict with analytics summary
        """
        try:
            query = """
                SELECT 
                    action,
                    COUNT(*) as count,
                    MAX(created_at) as last_event
                FROM iosapp.user_analytics
                WHERE device_id = $1 AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY action
                ORDER BY count DESC
            """ % days
            
            result = await db_manager.execute_query(query, device_id)
            
            # Process results
            actions = {}
            total_events = 0
            
            for row in result:
                actions[row['action']] = {
                    'count': row['count'],
                    'last_event': row['last_event'].isoformat() if row['last_event'] else None
                }
                total_events += row['count']
            
            return {
                'total_events': total_events,
                'actions': actions,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics for device {device_id}: {e}")
            return {'total_events': 0, 'actions': {}, 'period_days': days}
    
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