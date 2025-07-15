"""
Minimal notification service with hash-based deduplication
Works with truncate/load scraper approach
"""
import logging
import json
import hashlib
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.database import db_manager
from app.services.push_notifications import PushNotificationService
from app.services.privacy_analytics_service import privacy_analytics_service

logger = logging.getLogger(__name__)

class MinimalNotificationService:
    def __init__(self):
        self.push_service = PushNotificationService()
    
    @staticmethod
    def generate_job_hash(job_title: str, company: str) -> str:
        """Generate SHA-256 hash for job deduplication"""
        try:
            # Normalize inputs
            title = (job_title or "").strip().lower()
            comp = (company or "").strip().lower()
            
            # Create hash input
            hash_input = f"{title}|{comp}".encode('utf-8')
            
            # Generate SHA-256 hash
            return hashlib.sha256(hash_input).hexdigest()
        except Exception as e:
            logger.error(f"Error generating job hash: {e}")
            return hashlib.sha256(f"error|{str(e)}".encode()).hexdigest()
    
    async def is_notification_already_sent(self, device_id: str, job_hash: str) -> bool:
        """Check if notification was already sent to device"""
        try:
            query = """
                SELECT 1 FROM iosapp.notification_hashes 
                WHERE device_id = $1 AND job_hash = $2
                LIMIT 1
            """
            result = await db_manager.execute_query(query, device_id, job_hash)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking notification hash: {e}")
            return False  # If error, allow sending to be safe
    
    async def record_notification_sent(self, device_id: str, job_hash: str, 
                                     job_title: str, company: str, 
                                     job_source: str, matched_keywords: List[str]) -> bool:
        """Record that notification was sent"""
        try:
            query = """
                INSERT INTO iosapp.notification_hashes 
                (device_id, job_hash, job_title, job_company, job_source, matched_keywords)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (device_id, job_hash) DO NOTHING
                RETURNING id
            """
            
            result = await db_manager.execute_query(
                query, device_id, job_hash, job_title, company, 
                job_source, json.dumps(matched_keywords)
            )
            
            # Record analytics
            if result:
                await self.track_notification_sent(device_id, matched_keywords)
            
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error recording notification: {e}")
            return False
    
    async def track_notification_sent(self, device_id: str, matched_keywords: List[str]):
        """Track notification in analytics (with consent check)"""
        try:
            await privacy_analytics_service.track_action_with_consent(
                device_id,
                'notification_received',
                {
                    "matched_keywords": matched_keywords,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error tracking notification analytics: {e}")
    
    async def get_active_devices_with_keywords(self) -> List[Dict[str, Any]]:
        """Get all active devices with their keywords for notification matching"""
        try:
            query = """
                SELECT id, device_token, keywords
                FROM iosapp.device_users
                WHERE notifications_enabled = true 
                AND jsonb_array_length(keywords) > 0
            """
            
            result = await db_manager.execute_query(query)
            
            devices = []
            for row in result:
                try:
                    keywords_raw = row['keywords']
                    
                    # Handle JSONB field properly - same logic as chatbot
                    if keywords_raw is None:
                        keywords = []
                    elif isinstance(keywords_raw, list):
                        keywords = keywords_raw  # Already a list
                    elif isinstance(keywords_raw, str):
                        # Handle JSON string from database
                        try:
                            parsed = json.loads(keywords_raw)
                            keywords = parsed if isinstance(parsed, list) else [str(parsed)]
                        except (json.JSONDecodeError, TypeError):
                            # Fallback: treat as single keyword
                            keywords = [keywords_raw] if keywords_raw.strip() else []
                    else:
                        # Handle other types (e.g., dict, number)
                        keywords = []
                    
                    if keywords:  # Only include devices with keywords
                        devices.append({
                            'device_id': str(row['id']),
                            'device_token': row['device_token'],
                            'keywords': keywords
                        })
                except Exception as e:
                    logger.error(f"Error processing keywords for device {row['id']}: {e}")
                    continue
            
            logger.info(f"Found {len(devices)} active devices with keywords")
            return devices
            
        except Exception as e:
            logger.error(f"Error getting active devices: {e}")
            return []
    
    def match_keywords(self, job: Dict[str, Any], user_keywords: List[str]) -> List[str]:
        """Check if job matches user keywords"""
        try:
            # Get job text fields
            job_title = (job.get('title') or '').lower()
            job_company = (job.get('company') or '').lower()
            job_description = (job.get('description') or '').lower()
            
            # Combine all searchable text
            job_text = f"{job_title} {job_company} {job_description}"
            
            matched = []
            for keyword in user_keywords:
                if keyword.lower().strip() in job_text:
                    matched.append(keyword)
            
            return matched
        except Exception as e:
            logger.error(f"Error matching keywords: {e}")
            return []
    
    async def send_job_notification(self, device_token: str, device_id: str, 
                                  job: Dict[str, Any], matched_keywords: List[str]) -> bool:
        """Send job notification to device"""
        try:
            # Generate unique match ID for this notification
            job_hash = self.generate_job_hash(
                job.get('title', ''), 
                job.get('company', '')
            )
            
            success = await self.push_service.send_job_match_notification(
                device_token=device_token,
                device_id=device_id,
                job=job,
                matched_keywords=matched_keywords,
                match_id=job_hash[:16]  # First 16 chars as match ID
            )
            
            if success:
                logger.debug(f"Sent notification to device {device_id[:8]}... for job: {job.get('title', '')[:50]}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending job notification: {e}")
            return False
    
    async def process_job_notifications(self, jobs: List[Dict[str, Any]], 
                                      source_filter: Optional[str] = None,
                                      dry_run: bool = False) -> Dict[str, int]:
        """
        Process job notifications for all active devices - EFFICIENT VERSION
        Send ONE summary notification per device instead of individual notifications for each job
        
        Args:
            jobs: List of job dictionaries from scraper
            source_filter: Optional source filter (e.g., 'linkedin', 'indeed')
            dry_run: If True, don't send actual notifications
        
        Returns:
            Dict with stats: processed_jobs, matched_devices, notifications_sent
        """
        try:
            logger.info(f"Processing {len(jobs)} jobs for notifications (dry_run={dry_run})")
            
            # Get active devices
            devices = await self.get_active_devices_with_keywords()
            if not devices:
                logger.warning("No active devices with keywords found")
                return {"processed_jobs": 0, "matched_devices": 0, "notifications_sent": 0}
            
            stats = {
                "processed_jobs": len(jobs),
                "matched_devices": 0,
                "notifications_sent": 0,
                "errors": 0
            }
            
            # Process each device to find matches
            for device in devices:
                try:
                    device_id = device['device_id']
                    device_token = device['device_token']
                    user_keywords = device['keywords']
                    
                    logger.info(f"Processing device {device_id[:8]}... with keywords: {user_keywords}")
                    
                    # Find ALL matching jobs for this device
                    matching_jobs = []
                    all_matched_keywords = set()
                    
                    for job in jobs:
                        try:
                            # Apply source filter if specified
                            if source_filter and job.get('source', '').lower() != source_filter.lower():
                                continue
                            
                            # Check if job matches user keywords
                            matched_keywords = self.match_keywords(job, user_keywords)
                            
                            if matched_keywords:
                                job_hash = self.generate_job_hash(job.get('title', ''), job.get('company', ''))
                                
                                # Check if already notified
                                already_sent = await self.is_notification_already_sent(device_id, job_hash)
                                if not already_sent:
                                    matching_jobs.append(job)
                                    all_matched_keywords.update(matched_keywords)
                                    
                                    # Record that we'll notify about this job (prevent duplicates)
                                    if not dry_run:
                                        await self.record_notification_sent(
                                            device_id, job_hash, 
                                            job.get('title', ''), job.get('company', ''),
                                            job.get('source', ''), matched_keywords
                                        )
                        except Exception as e:
                            logger.error(f"Error processing job {job.get('id', 'unknown')} for device {device_id}: {e}")
                            continue
                    
                    # Send ONE notification per device if there are matches
                    if matching_jobs:
                        stats["matched_devices"] += 1
                        
                        logger.info(f"Device {device_id[:8]}... has {len(matching_jobs)} new job matches")
                        
                        if not dry_run:
                            # Send summary notification
                            success = await self.send_summary_notification(
                                device_token, device_id, len(matching_jobs), list(all_matched_keywords), matching_jobs[:3]
                            )
                            
                            if success:
                                stats["notifications_sent"] += 1
                                logger.info(f"✅ Sent summary notification to device {device_id[:8]}...")
                            else:
                                stats["errors"] += 1
                                logger.error(f"❌ Failed to send notification to device {device_id[:8]}...")
                        else:
                            # Dry run - just count
                            stats["notifications_sent"] += 1
                            logger.info(f"DRY RUN: Would send summary notification to device {device_id[:8]}... for {len(matching_jobs)} jobs")
                    else:
                        logger.info(f"No new matches for device {device_id[:8]}...")
                
                except Exception as e:
                    logger.error(f"Error processing device {device.get('device_id', 'unknown')}: {e}")
                    stats["errors"] += 1
                    continue
            
            logger.info(f"Notification processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in process_job_notifications: {e}")
            return {"processed_jobs": 0, "matched_devices": 0, "notifications_sent": 0, "errors": 1}
    
    async def send_summary_notification(self, device_token: str, device_id: str, 
                                      job_count: int, matched_keywords: List[str], 
                                      sample_jobs: List[Dict[str, Any]]) -> bool:
        """Send one summary notification instead of individual job notifications"""
        try:
            # Create summary job for notification
            summary_job = {
                "id": "summary",
                "title": f"{job_count} New Job{'s' if job_count != 1 else ''} Found!",
                "company": f"Matching: {', '.join(matched_keywords[:3])}",
                "source": "job_summary",
                "apply_link": "",
                "posted_at": datetime.now().isoformat()
            }
            
            success = await self.send_job_notification(
                device_token, device_id, summary_job, matched_keywords[:5]  # Limit keywords
            )
            
            return success
        except Exception as e:
            logger.error(f"Error sending summary notification: {e}")
            return False
    
    async def cleanup_old_notification_hashes(self, days_old: int = 30) -> int:
        """Clean up old notification hashes to prevent table growth"""
        try:
            query = """
                DELETE FROM iosapp.notification_hashes 
                WHERE sent_at < NOW() - INTERVAL '%s days'
                RETURNING id
            """ % days_old
            
            result = await db_manager.execute_query(query)
            deleted_count = len(result)
            
            logger.info(f"Cleaned up {deleted_count} notification hashes older than {days_old} days")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up notification hashes: {e}")
            return 0
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            # Get summary from view
            summary = await db_manager.execute_query("SELECT * FROM iosapp.analytics_summary")
            
            # Get recent notification activity
            recent_activity = await db_manager.execute_query("""
                SELECT 
                    DATE(sent_at) as date,
                    COUNT(*) as notifications_sent,
                    COUNT(DISTINCT device_id) as devices_notified
                FROM iosapp.notification_hashes 
                WHERE sent_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(sent_at)
                ORDER BY date DESC
            """)
            
            return {
                "summary": dict(summary[0]) if summary else {},
                "recent_activity": [dict(row) for row in recent_activity]
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {"summary": {}, "recent_activity": []}

# Global instance
minimal_notification_service = MinimalNotificationService()