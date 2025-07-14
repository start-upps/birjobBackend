"""
Privacy-compliant analytics service
GDPR/CCPA compliant analytics tracking with user consent
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from app.core.database import db_manager

logger = logging.getLogger(__name__)

class PrivacyAnalyticsService:
    """GDPR/CCPA compliant analytics service with consent management"""
    
    async def check_analytics_consent(self, device_id: str) -> bool:
        """
        Check if user has consented to analytics tracking
        
        Args:
            device_id: UUID of the device user
            
        Returns:
            bool: True if user has consented, False otherwise
        """
        try:
            query = """
                SELECT analytics_consent 
                FROM iosapp.device_users 
                WHERE id = $1
            """
            
            result = await db_manager.execute_query(query, device_id)
            
            if result and result[0]['analytics_consent']:
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking analytics consent for device {device_id}: {e}")
            return False
    
    async def track_action_with_consent(self, device_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track user action only if user has consented to analytics
        
        Args:
            device_id: UUID of the device user
            action: Action type (e.g., 'profile_view', 'preferences_update')
            metadata: Optional metadata dict
            
        Returns:
            bool: True if tracked (or skipped due to no consent), False if error
        """
        try:
            # Check consent first
            has_consent = await self.check_analytics_consent(device_id)
            
            if not has_consent:
                logger.debug(f"Skipping analytics tracking for device {device_id} - no consent")
                return True  # Not an error, just no consent
            
            # User has consented, track the action
            metadata_json = json.dumps(metadata or {})
            
            query = """
                INSERT INTO iosapp.user_analytics (device_id, action, metadata, created_at)
                VALUES ($1, $2, $3, NOW())
            """
            
            await db_manager.execute_command(query, device_id, action, metadata_json)
            logger.debug(f"Analytics tracked for device {device_id}: {action}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track action {action} for device {device_id}: {e}")
            return False
    
    async def set_analytics_consent(self, device_id: str, consent: bool, privacy_policy_version: str = "1.0") -> bool:
        """
        Set user's analytics consent preference
        
        Args:
            device_id: UUID of the device user
            consent: True to consent, False to revoke
            privacy_policy_version: Version of privacy policy user agreed to
            
        Returns:
            bool: True if updated successfully
        """
        try:
            if consent:
                # User is giving consent
                query = """
                    UPDATE iosapp.device_users 
                    SET analytics_consent = $2, 
                        consent_date = NOW(), 
                        privacy_policy_version = $3
                    WHERE id = $1
                """
                await db_manager.execute_command(query, device_id, consent, privacy_policy_version)
                logger.info(f"Analytics consent granted for device {device_id}")
            else:
                # User is revoking consent - delete existing analytics data
                await self.delete_analytics_data(device_id)
                
                query = """
                    UPDATE iosapp.device_users 
                    SET analytics_consent = $2, 
                        consent_date = NULL, 
                        privacy_policy_version = $3
                    WHERE id = $1
                """
                await db_manager.execute_command(query, device_id, consent, privacy_policy_version)
                logger.info(f"Analytics consent revoked and data deleted for device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set analytics consent for device {device_id}: {e}")
            return False
    
    async def delete_analytics_data(self, device_id: str) -> int:
        """
        Delete all analytics data for a user (GDPR right to be forgotten)
        
        Args:
            device_id: UUID of the device user
            
        Returns:
            int: Number of records deleted
        """
        try:
            query = """
                DELETE FROM iosapp.user_analytics 
                WHERE device_id = $1
            """
            
            result = await db_manager.execute_command(query, device_id)
            logger.info(f"Deleted analytics data for device {device_id}")
            
            # Return count would need a different approach with asyncpg
            return result if isinstance(result, int) else 0
            
        except Exception as e:
            logger.error(f"Failed to delete analytics data for device {device_id}: {e}")
            return 0
    
    async def get_analytics_summary_anonymous(self) -> Dict[str, Any]:
        """
        Get anonymous analytics summary (no user-identifiable data)
        Safe to show even to users who haven't consented
        
        Returns:
            Dict with anonymous analytics data
        """
        try:
            # Anonymous aggregated data only
            queries = {
                "total_active_users": "SELECT COUNT(DISTINCT device_id) as count FROM iosapp.user_analytics WHERE created_at > NOW() - INTERVAL '7 days'",
                "total_actions_7d": "SELECT COUNT(*) as count FROM iosapp.user_analytics WHERE created_at > NOW() - INTERVAL '7 days'",
                "popular_actions": """
                    SELECT action, COUNT(*) as count 
                    FROM iosapp.user_analytics 
                    WHERE created_at > NOW() - INTERVAL '7 days'
                    GROUP BY action 
                    ORDER BY count DESC 
                    LIMIT 5
                """
            }
            
            summary = {}
            
            for key, query in queries.items():
                try:
                    result = await db_manager.execute_query(query)
                    if key in ["total_active_users", "total_actions_7d"]:
                        summary[key] = result[0]['count'] if result else 0
                    else:
                        summary[key] = [dict(row) for row in result] if result else []
                except Exception as e:
                    logger.error(f"Error executing query {key}: {e}")
                    summary[key] = 0 if key in ["total_active_users", "total_actions_7d"] else []
            
            return {
                "anonymous_summary": summary,
                "period": "last_7_days",
                "privacy_note": "This data is anonymized and contains no user-identifiable information"
            }
            
        except Exception as e:
            logger.error(f"Failed to get anonymous analytics summary: {e}")
            return {
                "anonymous_summary": {},
                "error": "Failed to retrieve analytics data"
            }
    
    async def get_user_analytics_with_consent(self, device_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get user-specific analytics only if they have consented
        
        Args:
            device_id: UUID of the device user
            
        Returns:
            Tuple[bool, Dict]: (has_consent, analytics_data)
        """
        try:
            has_consent = await self.check_analytics_consent(device_id)
            
            if not has_consent:
                return False, {
                    "message": "Analytics data not available - user has not consented to tracking",
                    "consent_required": True
                }
            
            # User has consented, get their analytics
            query = """
                SELECT 
                    action,
                    COUNT(*) as count,
                    MAX(created_at) as last_event
                FROM iosapp.user_analytics
                WHERE device_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY action
                ORDER BY count DESC
            """
            
            result = await db_manager.execute_query(query, device_id)
            
            actions = {}
            total_events = 0
            
            for row in result:
                actions[row['action']] = {
                    'count': row['count'],
                    'last_event': row['last_event'].isoformat() if row['last_event'] else None
                }
                total_events += row['count']
            
            return True, {
                'total_events': total_events,
                'actions': actions,
                'period_days': 30,
                'consent_granted': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analytics for device {device_id}: {e}")
            return False, {"error": "Failed to retrieve analytics data"}
    
    async def export_user_data(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Export all user data for GDPR data portability requests
        
        Args:
            device_id: UUID of the device user
            
        Returns:
            Dict with all user data or None if no consent
        """
        try:
            # Check consent
            has_consent = await self.check_analytics_consent(device_id)
            
            if not has_consent:
                return {
                    "message": "No analytics data - user has not consented to tracking",
                    "consent_status": "not_consented"
                }
            
            # Get all user data
            analytics_query = """
                SELECT action, metadata, created_at 
                FROM iosapp.user_analytics
                WHERE device_id = $1
                ORDER BY created_at DESC
            """
            
            device_query = """
                SELECT device_token, keywords, notifications_enabled, analytics_consent, 
                       consent_date, privacy_policy_version, created_at
                FROM iosapp.device_users
                WHERE id = $1
            """
            
            analytics_data = await db_manager.execute_query(analytics_query, device_id)
            device_data = await db_manager.execute_query(device_query, device_id)
            
            return {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "device_info": dict(device_data[0]) if device_data else {},
                "analytics_events": [
                    {
                        "action": row['action'],
                        "metadata": row['metadata'],
                        "timestamp": row['created_at'].isoformat()
                    }
                    for row in analytics_data
                ],
                "total_events": len(analytics_data),
                "consent_status": "consented"
            }
            
        except Exception as e:
            logger.error(f"Failed to export user data for device {device_id}: {e}")
            return {"error": "Failed to export user data"}

# Global instance
privacy_analytics_service = PrivacyAnalyticsService()