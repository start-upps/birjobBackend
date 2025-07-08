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
        
        # Debug logging - temporarily use INFO level
        self.logger.info(f"Job text: '{job_text}'")
        self.logger.info(f"User keywords: {user_keywords}")
        
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
                    self.logger.info(f"Word boundary match: '{keyword_lower}' in '{job_text}'")
                elif len(keyword_lower) >= 3:  # For shorter keywords, allow substring match
                    matched_keywords.append(keyword)
                    self.logger.info(f"Substring match: '{keyword_lower}' in '{job_text}'")
        
        self.logger.info(f"Matched keywords: {matched_keywords}")
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
        job_id_or_unique_key, 
        job_title_or_data=None, 
        job_company=None, 
        job_source=None, 
        job_unique_key=None, 
        matched_keywords=None
    ) -> Optional[str]:
        """Record that user has been notified about this job and return the notification history ID"""
        try:
            # Handle both calling patterns:
            # 1. _record_notification(user_id, job_unique_key, job_data, matched_keywords)
            # 2. _record_notification(user_id, job_id, job_title, job_company, job_source, job_unique_key, matched_keywords)
            
            if isinstance(job_title_or_data, dict):
                # Pattern 1: job_data is a dictionary
                job_data = job_title_or_data
                actual_job_unique_key = job_id_or_unique_key
                actual_matched_keywords = job_company if job_company else []
                
                # Get the actual integer job ID from the job data
                job_id = job_data.get('id')
                # Ensure job_id is an integer
                if job_id is not None:
                    try:
                        job_id = int(job_id)
                    except (ValueError, TypeError):
                        job_id = None
                
                job_title = job_data.get('title')
                job_company_name = job_data.get('company')
                job_source_name = job_data.get('source')
            else:
                # Pattern 2: individual parameters
                # job_id_or_unique_key should be the actual integer job ID here
                job_id = job_id_or_unique_key
                # Ensure job_id is an integer
                if job_id is not None:
                    try:
                        job_id = int(job_id)
                    except (ValueError, TypeError):
                        job_id = None
                
                job_title = job_title_or_data
                job_company_name = job_company
                job_source_name = job_source
                actual_job_unique_key = job_unique_key
                actual_matched_keywords = matched_keywords if matched_keywords else []
            
            query = """
                INSERT INTO iosapp.job_notification_history 
                (user_id, job_unique_key, job_id, job_title, job_company, job_source, matched_keywords)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, job_unique_key) DO NOTHING
                RETURNING id
            """
            result = await db_manager.execute_query(
                query,
                user_id,
                actual_job_unique_key,
                job_id,
                job_title,
                job_company_name,
                job_source_name,
                json.dumps(actual_matched_keywords)
            )
            if result:
                return str(result[0]['id'])
            return None
        except Exception as e:
            self.logger.error(f"Error recording notification: {e}")
            return None
    
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
    
    async def _get_recent_jobs(self, limit: int = None, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ALL recent jobs from the scraper database"""
        try:
            # Base query to get ALL recent jobs - using actual schema
            base_query = """
                SELECT 
                    id, title, company, apply_link, source, created_at
                FROM scraper.jobs_jobpost
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
            """
            
            params = []
            if source_filter:
                base_query += " AND source = $1"
                params.append(source_filter)
            
            # Only add LIMIT if explicitly specified and not None
            if limit is not None and limit > 0:
                base_query += " LIMIT $" + str(len(params) + 1)
                params.append(limit)
            
            result = await db_manager.execute_query(base_query, *params)
            return result
        except Exception as e:
            self.logger.error(f"Error getting recent jobs: {e}")
            return []
    
    async def process_job_notifications(
        self, 
        source_filter: Optional[str] = None,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Process job notifications for all active users - scans ALL jobs by default"""
        
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
            if limit:
                self.logger.info(f"Getting recent jobs (limit: {limit})...")
            else:
                self.logger.info("Getting ALL recent jobs from last 24 hours...")
            recent_jobs = await self._get_recent_jobs(limit, source_filter)
            self.logger.info(f"Found {len(recent_jobs)} recent jobs")
            
            if not recent_jobs:
                return stats
            
            # Group matches by user for bulk notifications
            user_job_matches = {}  # user_id -> list of job matches
            
            self.logger.info("Pre-processing job-user matches...")
            
            for job in recent_jobs:
                stats['processed_jobs'] += 1
                
                # Convert Record object to dict for easier access
                job_dict = dict(job) if hasattr(job, 'keys') else job
                
                job_unique_key = self._generate_job_unique_key(
                    job_dict.get('title', ''), 
                    job_dict.get('company', '')
                )
                
                # Check each user for keyword matches
                for user in active_users:
                    user_keywords = user.get('keywords', [])
                    if not user_keywords:
                        continue
                    
                    # Check for keyword matches first (cheaper than DB query)
                    matched_keywords = self._match_keywords(job_dict, user_keywords)
                    
                    if matched_keywords:
                        user_id = user['user_id']
                        
                        # Check if user already notified about this job
                        if not await self._has_been_notified(user_id, job_unique_key):
                            if user_id not in user_job_matches:
                                user_job_matches[user_id] = {
                                    'user': user,
                                    'jobs': []
                                }
                            
                            user_job_matches[user_id]['jobs'].append({
                                'job_dict': job_dict,
                                'job_unique_key': job_unique_key,
                                'matched_keywords': matched_keywords
                            })
            
            self.logger.info(f"Found {len(user_job_matches)} users with job matches")
            
            # Send bulk notifications per user
            for user_id, user_matches in user_job_matches.items():
                user = user_matches['user']
                jobs = user_matches['jobs']
                
                if not jobs:
                    continue
                
                stats['matched_users'] += len(jobs)
                
                # Record all notifications for this user
                notification_ids = []
                for job_match in jobs:
                    notification_id = await self._record_notification(
                        user_id,
                        job_match['job_unique_key'],
                        job_match['job_dict'],
                        job_match['matched_keywords']
                    )
                    if notification_id:
                        notification_ids.append(notification_id)
                
                # Send bulk notification to user
                if not dry_run and notification_ids:
                    try:
                        success = await self.push_service.send_bulk_job_notifications(
                            device_token=user['device_token'],
                            device_id=user['device_id'],
                            jobs=jobs,
                            notification_ids=notification_ids
                        )
                        
                        if success:
                            stats['notifications_sent'] += len(jobs)
                            self.logger.info(f"Sent bulk notification to user {user_id} for {len(jobs)} jobs")
                        else:
                            stats['errors'] += len(jobs)
                            self.logger.warning(f"Failed to send bulk notification to user {user_id}")
                            
                    except Exception as e:
                        stats['errors'] += len(jobs)
                        self.logger.error(f"Error sending bulk notification to user {user_id}: {e}")
                else:
                    stats['notifications_sent'] += len(jobs)  # Count as sent in dry run
                    self.logger.info(f"DRY RUN: Would send bulk notification to user {user_id} for {len(jobs)} jobs")
            
            self.logger.info(f"Bulk job notification processing completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error processing job notifications: {e}")
            stats['errors'] += 1
            return stats
    
    async def _send_notification_with_error_handling(
        self, 
        user: Dict[str, Any], 
        job_dict: Dict[str, Any], 
        matched_keywords: List[str], 
        notification_history_id: str
    ) -> bool:
        """Send notification with error handling"""
        try:
            success = await self.push_service.send_job_match_notification(
                device_token=user['device_token'],
                device_id=user['device_id'],
                job=job_dict,
                matched_keywords=matched_keywords,
                match_id=notification_history_id
            )
            
            if success:
                self.logger.info(f"Sent notification to user {user['user_id']} for job {job_dict.get('id')}")
            else:
                self.logger.warning(f"Failed to send notification to user {user['user_id']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
    
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
            notification_history_id = await self._record_notification(
                user_data['user_id'],
                job_unique_key,
                job_data,
                matched_keywords or []
            )
            
            if not notification_history_id:
                self.logger.info(f"User {user_data['user_id']} already notified about this job")
                return False
            
            # Send notification
            success = await self.push_service.send_job_match_notification(
                device_token=user_data['device_token'],
                device_id=user_data['device_id'],
                job=job_data,
                matched_keywords=matched_keywords or [],
                match_id=notification_history_id
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