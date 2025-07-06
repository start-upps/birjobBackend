import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

from app.core.database import db_manager
from app.services.push_notifications import PushNotificationService

logger = logging.getLogger(__name__)

class JobNotificationService:
    """Service for matching jobs to user keywords and sending notifications"""
    
    def __init__(self):
        self.push_service = PushNotificationService()
        self.logger = logging.getLogger(__name__)
    
    def _generate_job_unique_key(self, job_title: str, job_company: str) -> str:
        """Generate unique key for job based on title and company"""
        # Normalize title and company
        normalized_title = re.sub(r'[^a-zA-Z0-9\s]', '', job_title.lower().strip())
        normalized_company = re.sub(r'[^a-zA-Z0-9\s]', '', job_company.lower().strip())
        
        # Create hash from normalized strings
        combined = f"{normalized_company}_{normalized_title}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _match_keywords(self, job_data: Dict[str, Any], user_keywords: List[str]) -> List[str]:
        """Check if job matches user keywords"""
        matched_keywords = []
        
        # Combine job fields for matching - using available fields only
        job_text = " ".join([
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('source', '')
        ]).lower()
        
        # Check each keyword
        for keyword in user_keywords:
            if not keyword:
                continue
                
            keyword_lower = keyword.lower().strip()
            
            # Support both exact match and word boundary match
            if keyword_lower in job_text:
                # Check if it's a word boundary match (not just substring)
                if re.search(r'\b' + re.escape(keyword_lower) + r'\b', job_text):
                    matched_keywords.append(keyword)
                elif len(keyword_lower) >= 3:  # For shorter keywords, allow substring match
                    matched_keywords.append(keyword)
        
        return matched_keywords
    
    async def _has_been_notified(self, user_id: str, job_unique_key: str) -> bool:
        """Check if user has already been notified about this job"""
        try:
            query = """
                SELECT 1 FROM iosapp.job_notification_history 
                WHERE user_id = $1 AND job_unique_key = $2
                LIMIT 1
            """
            result = await db_manager.execute_query(query, user_id, job_unique_key)
            return len(result) > 0
        except Exception as e:
            self.logger.error(f"Error checking notification history: {e}")
            return False
    
    async def _record_notification(
        self, 
        user_id: str, 
        job_unique_key: str, 
        job_data: Dict[str, Any], 
        matched_keywords: List[str]
    ) -> bool:
        """Record that user has been notified about this job"""
        try:
            query = """
                INSERT INTO iosapp.job_notification_history 
                (user_id, job_unique_key, job_id, job_title, job_company, job_source, matched_keywords)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, job_unique_key) DO NOTHING
            """
            await db_manager.execute_command(
                query,
                user_id,
                job_unique_key,
                job_data.get('id'),
                job_data.get('title'),
                job_data.get('company'),
                job_data.get('source'),
                json.dumps(matched_keywords)
            )
            return True
        except Exception as e:
            self.logger.error(f"Error recording notification: {e}")
            return False
    
    async def _get_active_users_with_keywords(self) -> List[Dict[str, Any]]:
        """Get all active users with their keywords and device tokens"""
        try:
            query = """
                SELECT DISTINCT
                    u.id as user_id,
                    u.keywords,
                    u.notifications_enabled,
                    dt.device_token,
                    dt.device_id
                FROM iosapp.users u
                JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                WHERE u.notifications_enabled = true 
                    AND dt.is_active = true
                    AND u.keywords IS NOT NULL
                    AND jsonb_array_length(u.keywords) > 0
            """
            result = await db_manager.execute_query(query)
            return result
        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            return []
    
    async def _get_recent_jobs(self, limit: int = 100, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent jobs from the scraper database"""
        try:
            # Base query to get recent jobs - using actual schema
            base_query = """
                SELECT 
                    id, title, company, apply_link, source, created_at
                FROM scraper.jobs_jobpost
                WHERE created_at >= NOW() - INTERVAL '2 hours'
            """
            
            params = []
            if source_filter:
                base_query += " AND source = $1"
                params.append(source_filter)
            
            base_query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            result = await db_manager.execute_query(base_query, *params)
            return result
        except Exception as e:
            self.logger.error(f"Error getting recent jobs: {e}")
            return []
    
    async def process_job_notifications(
        self, 
        source_filter: Optional[str] = None,
        limit: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Process job notifications for all active users"""
        
        stats = {
            'processed_jobs': 0,
            'matched_users': 0,
            'notifications_sent': 0,
            'errors': 0
        }
        
        try:
            # Get active users with keywords
            self.logger.info("Getting active users with keywords...")
            active_users = await self._get_active_users_with_keywords()
            self.logger.info(f"Found {len(active_users)} active users")
            
            if not active_users:
                return stats
            
            # Get recent jobs
            self.logger.info(f"Getting recent jobs (limit: {limit})...")
            recent_jobs = await self._get_recent_jobs(limit, source_filter)
            self.logger.info(f"Found {len(recent_jobs)} recent jobs")
            
            if not recent_jobs:
                return stats
            
            # Process each job against all users
            for job in recent_jobs:
                stats['processed_jobs'] += 1
                job_unique_key = self._generate_job_unique_key(
                    job.get('title', ''), 
                    job.get('company', '')
                )
                
                matched_users_for_job = 0
                
                # Check each user for keyword matches
                for user in active_users:
                    user_keywords = user.get('keywords', [])
                    if not user_keywords:
                        continue
                    
                    # Check if user has already been notified about this job
                    if await self._has_been_notified(user['user_id'], job_unique_key):
                        continue
                    
                    # Check for keyword matches
                    matched_keywords = self._match_keywords(job, user_keywords)
                    
                    if matched_keywords:
                        matched_users_for_job += 1
                        
                        # Record notification (even in dry run to prevent duplicates)
                        await self._record_notification(
                            user['user_id'],
                            job_unique_key,
                            job,
                            matched_keywords
                        )
                        
                        # Send notification if not dry run
                        if not dry_run:
                            try:
                                success = await self.push_service.send_job_match_notification(
                                    device_token=user['device_token'],
                                    device_id=user['device_id'],
                                    job=job,
                                    matched_keywords=matched_keywords,
                                    match_id=job_unique_key
                                )
                                
                                if success:
                                    stats['notifications_sent'] += 1
                                    self.logger.info(f"Sent notification to user {user['user_id']} for job {job.get('id')}")
                                else:
                                    stats['errors'] += 1
                                    self.logger.warning(f"Failed to send notification to user {user['user_id']}")
                                    
                            except Exception as e:
                                stats['errors'] += 1
                                self.logger.error(f"Error sending notification: {e}")
                        else:
                            stats['notifications_sent'] += 1  # Count as sent in dry run
                            self.logger.info(f"DRY RUN: Would send notification to user {user['user_id']} for job {job.get('id')}")
                
                if matched_users_for_job > 0:
                    stats['matched_users'] += matched_users_for_job
                    self.logger.info(f"Job {job.get('id')} matched {matched_users_for_job} users")
            
            self.logger.info(f"Job notification processing completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error processing job notifications: {e}")
            stats['errors'] += 1
            return stats
    
    async def send_single_job_notification(
        self, 
        device_id: str, 
        job_id: int,
        job_title: str,
        job_company: str,
        job_source: Optional[str] = None,
        matched_keywords: List[str] = None
    ) -> bool:
        """Send notification for a single job match"""
        try:
            # Get user and device info
            user_query = """
                SELECT u.id as user_id, dt.device_token, dt.device_id
                FROM iosapp.users u
                JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                WHERE dt.device_id = $1 AND dt.is_active = true AND u.notifications_enabled = true
            """
            user_result = await db_manager.execute_query(user_query, device_id)
            
            if not user_result:
                self.logger.warning(f"No active user found for device {device_id}")
                return False
            
            user_data = user_result[0]
            job_unique_key = self._generate_job_unique_key(job_title, job_company)
            
            # Check if already notified
            if await self._has_been_notified(user_data['user_id'], job_unique_key):
                self.logger.info(f"User {user_data['user_id']} already notified about this job")
                return False
            
            # Create job data for notification
            job_data = {
                'id': job_id,
                'title': job_title,
                'company': job_company,
                'source': job_source
            }
            
            # Record notification
            await self._record_notification(
                user_data['user_id'],
                job_unique_key,
                job_data,
                matched_keywords or []
            )
            
            # Send notification
            success = await self.push_service.send_job_match_notification(
                device_token=user_data['device_token'],
                device_id=user_data['device_id'],
                job=job_data,
                matched_keywords=matched_keywords or [],
                match_id=job_unique_key
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending single job notification: {e}")
            return False
    
    async def get_user_notification_history(
        self, 
        device_id: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get notification history for a user"""
        try:
            # Get user ID
            user_query = """
                SELECT u.id as user_id FROM iosapp.users u
                JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                WHERE dt.device_id = $1
            """
            user_result = await db_manager.execute_query(user_query, device_id)
            
            if not user_result:
                return {"user_id": None, "total_notifications": 0, "recent_notifications": []}
            
            user_id = user_result[0]['user_id']
            
            # Get notification history
            history_query = """
                SELECT 
                    job_id, job_title, job_company, job_source, 
                    matched_keywords, notification_sent_at
                FROM iosapp.job_notification_history
                WHERE user_id = $1
                ORDER BY notification_sent_at DESC
                LIMIT $2
            """
            history_result = await db_manager.execute_query(history_query, user_id, limit)
            
            # Get total count
            count_query = """
                SELECT COUNT(*) as total FROM iosapp.job_notification_history
                WHERE user_id = $1
            """
            count_result = await db_manager.execute_query(count_query, user_id)
            total_count = count_result[0]['total'] if count_result else 0
            
            # Format history
            formatted_history = []
            for record in history_result:
                formatted_history.append({
                    'job_id': record['job_id'],
                    'job_title': record['job_title'],
                    'job_company': record['job_company'],
                    'job_source': record['job_source'],
                    'matched_keywords': json.loads(record['matched_keywords']) if record['matched_keywords'] else [],
                    'notification_sent_at': record['notification_sent_at'].isoformat() if record['notification_sent_at'] else None
                })
            
            return {
                'user_id': str(user_id),
                'total_notifications': total_count,
                'recent_notifications': formatted_history
            }
            
        except Exception as e:
            self.logger.error(f"Error getting notification history: {e}")
            return {"user_id": None, "total_notifications": 0, "recent_notifications": []}
    
    async def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old notification history records"""
        try:
            query = """
                DELETE FROM iosapp.job_notification_history
                WHERE notification_sent_at < NOW() - INTERVAL '%s days'
            """ % days_old
            
            result = await db_manager.execute_command(query)
            self.logger.info(f"Cleaned up notification history older than {days_old} days")
            return result
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old notifications: {e}")
            return 0

# Global instance
job_notification_service = JobNotificationService()