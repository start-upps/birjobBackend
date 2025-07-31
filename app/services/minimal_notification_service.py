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
import uuid

from app.core.database import db_manager
from app.core.redis_client import redis_client
from app.services.push_notifications import PushNotificationService
from app.services.privacy_analytics_service import privacy_analytics_service

logger = logging.getLogger(__name__)

class MinimalNotificationService:
    def __init__(self):
        self.push_service = PushNotificationService()
    
    @staticmethod
    def generate_job_hash(job_title: str, company: str) -> str:
        """Generate SHA-256 hash for job deduplication (truncated to 32 chars)"""
        try:
            # Normalize inputs
            title = (job_title or "").strip().lower()
            comp = (company or "").strip().lower()
            
            # Create hash input
            hash_input = f"{title}|{comp}".encode('utf-8')
            
            # Generate SHA-256 hash and truncate to 32 chars to fit DB column
            return hashlib.sha256(hash_input).hexdigest()[:32]
        except Exception as e:
            logger.error(f"Error generating job hash: {e}")
            return hashlib.sha256(f"error|{str(e)}".encode()).hexdigest()[:32]
    
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
                                     job_source: str, matched_keywords: List[str],
                                     apply_link: str = None, notification_id: str = None) -> bool:
        """Record that notification was sent - returns True if this is the first time"""
        try:
            # Log the notification_id for debugging iOS issues
            if notification_id:
                logger.info(f"📝 Recording notification: notification_id={notification_id}, job_hash={job_hash}")
            
            query = """
                INSERT INTO iosapp.notification_hashes 
                (device_id, job_hash, job_title, job_company, job_source, matched_keywords, apply_link)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (device_id, job_hash) DO NOTHING
                RETURNING id
            """
            
            result = await db_manager.execute_query(
                query, device_id, job_hash, job_title, company, 
                job_source, json.dumps(matched_keywords), apply_link
            )
            
            # If result is empty, notification already exists (duplicate)
            is_first_time = len(result) > 0
            
            if is_first_time:
                # Record analytics for new notifications only
                await self.track_notification_sent(device_id, matched_keywords)
                logger.debug(f"Recorded new notification for device {device_id[:8]}... job_hash: {job_hash}")
            else:
                logger.debug(f"Duplicate notification blocked for device {device_id[:8]}... job_hash: {job_hash}")
            
            return is_first_time
        except Exception as e:
            logger.error(f"Error recording notification for device {device_id[:8]}... job_hash: {job_hash}: {e}")
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
    
    async def create_job_match_session(self, device_id: str, matched_jobs: List[Dict[str, Any]], 
                                     matched_keywords: List[str]) -> str:
        """Create a job match session and store all matched jobs"""
        try:
            # Generate unique session ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"match_{timestamp}_{str(uuid.uuid4())[:8]}"
            
            # Create the session record
            session_query = """
                INSERT INTO iosapp.job_match_sessions 
                (session_id, device_id, total_matches, matched_keywords, notification_sent)
                VALUES ($1, $2, $3, $4, false)
                RETURNING session_id
            """
            
            session_result = await db_manager.execute_query(
                session_query, session_id, device_id, len(matched_jobs), 
                json.dumps(matched_keywords)
            )
            
            if not session_result:
                raise Exception("Failed to create job match session")
            
            # Store all matched jobs in the session
            for i, job in enumerate(matched_jobs):
                # CRITICAL FIX: Use original title for consistent session storage
                original_title = job.get('original_title') or job.get('title', '')
                job_hash = self.generate_job_hash(original_title, job.get('company', ''))
                
                job_insert_query = """
                    INSERT INTO iosapp.job_match_session_jobs 
                    (session_id, job_hash, job_title, job_company, job_source, apply_link, job_data, match_score)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (session_id, job_hash) DO NOTHING
                """
                
                await db_manager.execute_query(
                    job_insert_query,
                    session_id,
                    job_hash,
                    original_title[:500],  # Use original title for database consistency
                    job.get('company', '')[:200],
                    job.get('source', '')[:100],
                    job.get('apply_link', ''),
                    json.dumps(job),
                    1000 - i  # Higher score for earlier jobs (better matches)
                )
            
            logger.info(f"Created job match session {session_id} with {len(matched_jobs)} jobs for device {device_id[:8]}...")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating job match session: {e}")
            return None
    
    async def mark_session_notification_sent(self, session_id: str):
        """Mark that notification was sent for this session"""
        try:
            update_query = """
                UPDATE iosapp.job_match_sessions 
                SET notification_sent = true 
                WHERE session_id = $1
            """
            await db_manager.execute_query(update_query, session_id)
        except Exception as e:
            logger.error(f"Error marking session notification sent: {e}")
    
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
            # Generate unique match ID for this notification using ORIGINAL title
            # CRITICAL FIX: Always use original title for consistent hashing
            original_title = job.get('original_title') or job.get('title', '')
            job_hash = self.generate_job_hash(
                original_title, 
                job.get('company', '')
            )
            
            success, notification_id = await self.push_service.send_job_match_notification(
                device_token=device_token,
                device_id=device_id,
                job=job,
                matched_keywords=matched_keywords,
                match_id=job_hash  # Full hash for persistent reference
            )
            
            if success:
                logger.debug(f"Sent notification to device {device_id[:8]}... for job: {job.get('title', '')[:50]}")
                logger.info(f"🔔 Push notification sent with notification_id: {notification_id}")
                
                # Log critical iOS debugging info
                session_context = job.get('session_context', {})
                if session_context:
                    logger.info(f"📱 iOS DEBUG - Session context: session_id={session_context.get('session_id')}, total_matches={session_context.get('total_matches')}")
                else:
                    logger.warning(f"📱 iOS DEBUG - No session context found in job payload")
                
                logger.info(f"📱 iOS DEBUG - notification_id: {notification_id}, job_hash: {job_hash}")
                
                # Store notification with notification_id for iOS app lookup
                # CRITICAL FIX: Always use original title for database storage, not enhanced title
                original_title = job.get('original_title') or job.get('title', '')
                await self.record_notification_sent(
                    device_id, job_hash, 
                    original_title, job.get('company', ''),
                    job.get('source', ''), matched_keywords,
                    job.get('apply_link'), notification_id
                )
            
            return success
        except Exception as e:
            logger.error(f"Error sending job notification: {e}")
            return False
    
    async def process_job_notifications_parallel(self, jobs: List[Dict[str, Any]], 
                                               source_filter: Optional[str] = None,
                                               dry_run: bool = False) -> Dict[str, int]:
        """
        OPTIMIZED: Process job notifications in parallel with bulk operations
        Target: Complete 20+ users in under 2 minutes instead of 28 minutes
        """
        try:
            logger.info(f"🚀 OPTIMIZED: Processing {len(jobs)} jobs for notifications (dry_run={dry_run})")
            
            # Get active devices
            devices = await self.get_active_devices_with_keywords()
            if not devices:
                logger.warning("No active devices with keywords found")
                return {"processed_jobs": 0, "matched_devices": 0, "notifications_sent": 0}
            
            logger.info(f"📱 Processing {len(devices)} devices in parallel...")
            
            stats = {
                "processed_jobs": len(jobs),
                "matched_devices": 0,
                "notifications_sent": 0,
                "errors": 0
            }
            
            # Process ALL devices in parallel (no batching for max speed)
            logger.info(f"⚡ Processing ALL {len(devices)} devices in parallel...")
            
            # Create tasks for all devices at once
            device_tasks = [
                self._process_device_optimized(device, jobs, source_filter, dry_run)
                for device in devices
            ]
            
            # Process all devices simultaneously
            all_results = await asyncio.gather(*device_tasks, return_exceptions=True)
            
            # Aggregate results
            for result in all_results:
                if isinstance(result, Exception):
                    logger.error(f"Device processing error: {result}")
                    stats["errors"] += 1
                elif result:
                    if result.get("matched"):
                        stats["matched_devices"] += 1
                    if result.get("notification_sent"):
                        stats["notifications_sent"] += 1
            
            logger.info(f"✅ OPTIMIZED processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in parallel processing: {e}")
            return {"processed_jobs": 0, "matched_devices": 0, "notifications_sent": 0, "errors": 1}
    
    async def _process_device_optimized(self, device: Dict, jobs: List[Dict], 
                                       source_filter: Optional[str], dry_run: bool) -> Dict:
        """Process a single device with bulk operations for speed"""
        try:
            device_id = device['device_id']
            device_token = device['device_token']
            user_keywords = device['keywords']
            
            # Step 1: Bulk filter jobs by keywords (much faster than individual checks)
            matching_jobs = []
            job_hashes = []
            all_matched_keywords = set()
            
            for job in jobs:
                # Apply source filter
                if source_filter and job.get('source', '').lower() != source_filter.lower():
                    continue
                
                # Quick keyword matching
                matched_keywords = self.match_keywords(job, user_keywords)
                if matched_keywords:
                    # CRITICAL FIX: Use consistent original title for hashing and preserve it
                    job_copy = job.copy()  # Preserve original job data
                    job_copy['original_title'] = job.get('title', '')  # Store original title
                    job_hash = self.generate_job_hash(job.get('title', ''), job.get('company', ''))
                    matching_jobs.append(job_copy)
                    job_hashes.append(job_hash)
                    all_matched_keywords.update(matched_keywords)
            
            if not matching_jobs:
                return {"matched": False, "notification_sent": False}
            
            # Step 2: Bulk check for already sent notifications (single query)
            if not dry_run:
                already_sent_hashes = await self._bulk_check_notifications_sent(device_id, job_hashes)
                
                # Filter out already sent jobs
                new_jobs = []
                new_hashes = []
                for job, job_hash in zip(matching_jobs, job_hashes):
                    if job_hash not in already_sent_hashes:
                        new_jobs.append(job)
                        new_hashes.append(job_hash)
                
                if not new_jobs:
                    return {"matched": True, "notification_sent": False}
                
                # Step 3: Bulk record notifications (single query)
                await self._bulk_record_notifications(device_id, new_jobs, new_hashes, user_keywords)
                
                matching_jobs = new_jobs
            
            # Step 4: Send enhanced notification representing ALL jobs
            if matching_jobs:
                # CRITICAL FIX: Check if session already exists for this job set
                # Use primary job hash to prevent duplicate session notifications
                primary_original_title = matching_jobs[0].get('original_title') or matching_jobs[0].get('title', '')
                primary_job_hash = self.generate_job_hash(
                    primary_original_title, 
                    matching_jobs[0].get('company', '')
                )
                
                # Check for existing session notification with same primary job
                session_check_query = """
                    SELECT session_id FROM iosapp.job_match_sessions 
                    WHERE device_id = $1 AND notification_sent = true
                    AND session_id IN (
                        SELECT session_id FROM iosapp.job_match_session_jobs 
                        WHERE job_hash = $2
                    )
                    AND created_at > NOW() - INTERVAL '1 hour'
                    LIMIT 1
                """
                
                existing_sessions = await db_manager.execute_query(
                    session_check_query, device_id, primary_job_hash
                )
                
                if existing_sessions:
                    logger.info(f"🔄 Skipping - session notification already sent for primary job {primary_job_hash[:8]}...")
                    return {"matched": True, "notification_sent": False}
                
                session_id = await self.create_job_match_session(
                    device_id, matching_jobs, list(all_matched_keywords)
                )
                
                if session_id:
                    # Create enhanced notification showing job variety (not just first job)
                    enhanced_job = self._create_multi_job_notification(
                        matching_jobs, session_id, list(all_matched_keywords)
                    )
                    
                    success = await self.send_job_notification(
                        device_token, device_id, enhanced_job, list(all_matched_keywords)[:3]
                    )
                    
                    return {"matched": True, "notification_sent": success}
            
            return {"matched": True, "notification_sent": False}
            
        except Exception as e:
            logger.error(f"Error processing device {device_id[:8]}...: {e}")
            return {"matched": False, "notification_sent": False}
    
    async def _bulk_check_notifications_sent(self, device_id: str, job_hashes: List[str]) -> set:
        """Bulk check which notifications were already sent (single DB query)"""
        try:
            if not job_hashes:
                return set()
            
            # Use ANY() for efficient bulk check
            query = """
                SELECT job_hash FROM iosapp.notification_hashes 
                WHERE device_id = $1 AND job_hash = ANY($2)
            """
            result = await db_manager.execute_query(query, device_id, job_hashes)
            return {row['job_hash'] for row in result}
        except Exception as e:
            logger.error(f"Error in bulk notification check: {e}")
            return set()
    
    async def _bulk_record_notifications(self, device_id: str, jobs: List[Dict], 
                                        job_hashes: List[str], keywords: List[str]):
        """TRUE BULK record notifications (single DB query using executemany)"""
        try:
            if not jobs:
                return
            
            # Prepare all records for bulk insert
            records = []
            keywords_json = json.dumps(keywords[:3])  # Convert once
            
            for job, job_hash in zip(jobs, job_hashes):
                records.append((
                    device_id,
                    job_hash,
                    job.get('title', ''),
                    job.get('company', ''),
                    job.get('source', ''),
                    keywords_json,
                    job.get('apply_link')
                ))
            
            if records:
                # True bulk insert using executemany
                query = """
                    INSERT INTO iosapp.notification_hashes 
                    (device_id, job_hash, job_title, company, source, matched_keywords, apply_link, sent_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (device_id, job_hash) DO NOTHING
                """
                
                try:
                    # Use asyncpg's executemany for true bulk performance
                    pool = db_manager.pool
                    async with pool.acquire() as conn:
                        await conn.executemany(query, records)
                    
                    logger.debug(f"Bulk recorded {len(records)} notifications for device {device_id[:8]}...")
                except Exception as bulk_error:
                    # Fallback to individual inserts if bulk fails
                    logger.warning(f"Bulk insert failed, falling back to individual inserts: {bulk_error}")
                    for record in records:
                        try:
                            await db_manager.execute_command(query, *record)
                        except Exception as individual_error:
                            logger.error(f"Failed to record individual notification: {individual_error}")
                            
        except Exception as e:
            logger.error(f"Error in bulk notification recording: {e}")

    def _create_multi_job_notification(self, matching_jobs: List[Dict], session_id: str, 
                                     matched_keywords: List[str]) -> Dict:
        """Create notification payload that represents multiple jobs intelligently"""
        try:
            total_jobs = len(matching_jobs)
            
            if total_jobs == 1:
                # Single job - use it directly with original title preserved
                import copy
                primary_job = copy.deepcopy(matching_jobs[0])
                primary_job['original_title'] = primary_job.get('title', '')
            else:
                # Multiple jobs - create smart summary
                # Prioritize by: 1) More keywords matched, 2) Better company, 3) Newer
                
                # Get unique companies and titles for variety
                companies = list(set(job.get('company', 'Unknown') for job in matching_jobs[:5]))
                titles = list(set(job.get('title', 'Unknown') for job in matching_jobs[:5]))
                
                # Use the first job as base - DEEP COPY to prevent corruption of original data
                import copy
                primary_job = copy.deepcopy(matching_jobs[0])
                
                # Create enhanced title for NOTIFICATION ONLY (don't modify original)
                original_title = primary_job.get('title', 'Job')
                if total_jobs == 2:
                    enhanced_title = f"{original_title} + 1 more position"
                elif len(companies) > 1:
                    other_companies = companies[1:3]  # Show up to 2 other companies
                    companies_text = ", ".join(other_companies)
                    enhanced_title = f"{original_title} + {total_jobs-1} more at {companies_text}..."
                else:
                    enhanced_title = f"{original_title} + {total_jobs-1} similar positions"
                
                # CRITICAL FIX: Store original title separately for database consistency
                primary_job['original_title'] = original_title  # Always preserve original
                primary_job['notification_title'] = enhanced_title  # For push notification display
                primary_job['enhanced_summary'] = {
                    "total_companies": len(companies),
                    "company_variety": companies[:3],
                    "title_variety": titles[:3],
                    "top_keywords": matched_keywords[:3]
                }
                # Keep original title intact: primary_job['title'] stays unchanged
            
            # Add session context
            enhanced_job = {
                **primary_job,
                "session_context": {
                    "session_id": session_id,
                    "total_matches": total_jobs,
                    "additional_jobs": max(0, total_jobs - 1),
                    "matched_keywords": matched_keywords[:3],
                    "job_variety": {
                        "companies_count": len(set(job.get('company', '') for job in matching_jobs)),
                        "sources_count": len(set(job.get('source', '') for job in matching_jobs)),
                        "unique_titles": len(set(job.get('title', '') for job in matching_jobs[:10]))
                    }
                }
            }
            
            return enhanced_job
            
        except Exception as e:
            logger.error(f"Error creating multi-job notification: {e}")
            # Fallback to simple first job
            return {
                **matching_jobs[0],
                "session_context": {
                    "session_id": session_id,
                    "total_matches": len(matching_jobs),
                    "additional_jobs": len(matching_jobs) - 1,
                    "matched_keywords": matched_keywords[:3]
                }
            }

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
                                # CRITICAL FIX: Use consistent original title for hashing
                                job_hash = self.generate_job_hash(job.get('title', ''), job.get('company', ''))
                                
                                # Use distributed lock to prevent race conditions
                                lock_key = f"notification_lock:{device_id}:{job_hash}"
                                
                                if not dry_run:
                                    # Try to acquire lock for this notification
                                    try:
                                        async with redis_client.lock(lock_key, timeout=5):
                                            # Check if already sent (inside lock)
                                            already_sent = await self.is_notification_already_sent(device_id, job_hash)
                                            if not already_sent:
                                                # Record notification
                                                notification_recorded = await self.record_notification_sent(
                                                    device_id, job_hash, 
                                                    job.get('title', ''), job.get('company', ''),
                                                    job.get('source', ''), matched_keywords,
                                                    job.get('apply_link')
                                                )
                                                
                                                if notification_recorded:
                                                    job_copy = job.copy()
                                                    job_copy['original_title'] = job.get('title', '')
                                                    matching_jobs.append(job_copy)
                                                    all_matched_keywords.update(matched_keywords)
                                    except Exception as lock_error:
                                        logger.warning(f"Failed to acquire lock for {device_id}:{job_hash}: {lock_error}")
                                        # Fallback to database-only deduplication
                                        notification_recorded = await self.record_notification_sent(
                                            device_id, job_hash, 
                                            job.get('title', ''), job.get('company', ''),
                                            job.get('source', ''), matched_keywords,
                                            job.get('apply_link')
                                        )
                                        
                                        if notification_recorded:
                                            job_copy = job.copy()
                                            job_copy['original_title'] = job.get('title', '')
                                            matching_jobs.append(job_copy)
                                            all_matched_keywords.update(matched_keywords)
                                else:
                                    # In dry run mode, still check if already sent
                                    already_sent = await self.is_notification_already_sent(device_id, job_hash)
                                    if not already_sent:
                                        job_copy = job.copy()
                                        job_copy['original_title'] = job.get('title', '')
                                        matching_jobs.append(job_copy)
                                        all_matched_keywords.update(matched_keywords)
                        except Exception as e:
                            logger.error(f"Error processing job {job.get('id', 'unknown')} for device {device_id}: {e}")
                            continue
                    
                    # Send ONE notification per device if there are matches
                    if matching_jobs:
                        stats["matched_devices"] += 1
                        
                        logger.info(f"Device {device_id[:8]}... has {len(matching_jobs)} new job matches")
                        
                        if not dry_run:
                            # CRITICAL FIX: Check for duplicate session notifications  
                            primary_original_title = matching_jobs[0].get('original_title') or matching_jobs[0].get('title', '')
                            primary_job_hash = self.generate_job_hash(
                                primary_original_title, 
                                matching_jobs[0].get('company', '')
                            )
                            
                            # Check for existing session notification with same primary job
                            session_check_query = """
                                SELECT session_id FROM iosapp.job_match_sessions 
                                WHERE device_id = $1 AND notification_sent = true
                                AND session_id IN (
                                    SELECT session_id FROM iosapp.job_match_session_jobs 
                                    WHERE job_hash = $2
                                )
                                AND created_at > NOW() - INTERVAL '1 hour'
                                LIMIT 1
                            """
                            
                            existing_sessions = await db_manager.execute_query(
                                session_check_query, device_id, primary_job_hash
                            )
                            
                            if existing_sessions:
                                logger.info(f"🔄 Skipping - session notification already sent for primary job {primary_job_hash[:8]}...")
                                continue  # Skip to next device
                            
                            # Create job match session to store all matched jobs
                            session_id = await self.create_job_match_session(
                                device_id, matching_jobs, list(all_matched_keywords)
                            )
                            
                            if session_id:
                                # Send enhanced notification representing ALL jobs (not just first)
                                enhanced_job = self._create_multi_job_notification(
                                    matching_jobs, session_id, list(all_matched_keywords)
                                )
                                
                                success = await self.send_job_notification(
                                    device_token, device_id, enhanced_job, list(all_matched_keywords)[:3]
                                )
                                
                                if success:
                                    # Mark session as notification sent
                                    await self.mark_session_notification_sent(session_id)
                            else:
                                success = False
                            
                            if success:
                                stats["notifications_sent"] += 1
                                logger.info(f"✅ Sent 1 smart notification ({len(matching_jobs)} matches) to device {device_id[:8]}...")
                            else:
                                stats["errors"] += 1
                                logger.error(f"❌ Failed to send notification to device {device_id[:8]}...")
                        else:
                            # Dry run - just count
                            stats["notifications_sent"] += 1
                            logger.info(f"DRY RUN: Would send 1 smart notification ({len(matching_jobs)} matches) to device {device_id[:8]}...")
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