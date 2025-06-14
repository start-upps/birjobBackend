import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import db_manager
from app.core.redis_client import redis_client
from app.core.monitoring import metrics
from app.services.push_notifications import PushNotificationService

logger = logging.getLogger(__name__)

class JobMatchEngine:
    """Core job matching engine that processes new jobs against device subscriptions"""
    
    def __init__(self):
        self.push_service = PushNotificationService()
        self.logger = logging.getLogger(__name__)
    
    async def process_new_jobs(self):
        """Main matching engine - processes all jobs since scraper runs every 4-5 hours"""
        try:
            # Since scraper truncates and refreshes all data every 4-5 hours,
            # we need to process ALL jobs, not just recent ones
            all_jobs = await self.get_all_jobs()
            if not all_jobs:
                self.logger.info("No jobs to process")
                return
            
            self.logger.info(f"Processing {len(all_jobs)} jobs against subscriptions")
            
            # Get all active subscriptions
            active_subscriptions = await self.get_active_subscriptions()
            
            if not active_subscriptions:
                self.logger.info("No active subscriptions found")
                return
            
            # Clean up old matches for jobs that no longer exist
            await self.cleanup_orphaned_matches()
            
            self.logger.info(f"Found {len(active_subscriptions)} active subscriptions")
            for sub in active_subscriptions:
                self.logger.info(f"  Device {sub['device_id']}: keywords={sub['keywords']}")
            
            matches_created = 0
            jobs_processed = 0
            for job in all_jobs:
                jobs_processed += 1
                if jobs_processed % 1000 == 0:  # Log progress every 1000 jobs
                    self.logger.info(f"Processed {jobs_processed}/{len(all_jobs)} jobs, created {matches_created} matches")
                    
                if await self.match_job_to_subscriptions(job, active_subscriptions):
                    matches_created += 1
            
            self.logger.info(f"Processing complete: {jobs_processed} jobs processed, {matches_created} new matches created")
                
        except Exception as e:
            self.logger.error(f"Error in match engine: {e}", exc_info=True)
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from scraper schema (since scraper refreshes all data)"""
        try:
            query = """
                SELECT id, title, company, apply_link, source, created_at
                FROM scraper.jobs_jobpost 
                ORDER BY created_at DESC
            """
            jobs = await db_manager.execute_query(query)
            return [dict(job) for job in jobs] if jobs else []
            
        except Exception as e:
            self.logger.error(f"Error fetching all jobs: {e}")
            return []
    
    async def cleanup_orphaned_matches(self):
        """Remove job matches for jobs that no longer exist (deleted by scraper truncate)"""
        try:
            query = """
                DELETE FROM iosapp.job_matches 
                WHERE job_id NOT IN (
                    SELECT id::text FROM scraper.jobs_jobpost
                )
            """
            result = await db_manager.execute_command(query)
            self.logger.info("Cleaned up orphaned job matches")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up orphaned matches: {e}")
    
    async def get_new_jobs_since(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get new jobs from scraper schema since cutoff time (legacy method)"""
        try:
            query = """
                SELECT id, title, company, apply_link, source, created_at
                FROM scraper.jobs_jobpost 
                WHERE created_at > $1
                ORDER BY created_at DESC
            """
            jobs = await db_manager.execute_query(query, cutoff_time)
            return [dict(job) for job in jobs] if jobs else []
            
        except Exception as e:
            self.logger.error(f"Error fetching new jobs: {e}")
            return []
    
    async def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all active device subscriptions with device tokens"""
        try:
            query = """
                SELECT 
                    ks.id,
                    ks.device_id,
                    ks.keywords,
                    ks.sources,
                    ks.location_filters,
                    dt.device_token
                FROM iosapp.keyword_subscriptions ks
                JOIN iosapp.device_tokens dt ON ks.device_id = dt.id
                WHERE ks.is_active = true 
                AND dt.is_active = true
            """
            subscriptions = await db_manager.execute_query(query)
            return [dict(sub) for sub in subscriptions] if subscriptions else []
            
        except Exception as e:
            self.logger.error(f"Error fetching active subscriptions: {e}")
            return []
    
    async def match_job_to_subscriptions(self, job: Dict[str, Any], subscriptions: List[Dict[str, Any]]) -> bool:
        """Match a single job against all active subscriptions. Returns True if any matches created."""
        # Only use title and company for matching since description column doesn't exist
        job_text = f"{job.get('title', '')} {job.get('company', '')}".lower()
        matches_created = False
        
        for subscription in subscriptions:
            try:
                # Check if match already exists for this job+device combination (replaces Redis check)
                if await self.match_already_exists(subscription['device_id'], job['id']):
                    continue
                
                # Apply source filter if specified
                if (subscription.get('sources') and 
                    job.get('source') not in subscription['sources']):
                    continue
                
                # Apply location filters if specified
                if not self.check_location_filters(job, subscription.get('location_filters')):
                    continue
                
                # Check keyword matches
                matched_keywords = []
                for keyword in subscription['keywords']:
                    if keyword.lower() in job_text:
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    # Calculate relevance score
                    relevance_score = self.calculate_relevance(
                        job, matched_keywords, subscription['keywords']
                    )
                    
                    # Only proceed if relevance score meets minimum threshold
                    if relevance_score >= 0.1:  # Lowered threshold for better matching
                        # Store match in database
                        match_id = await self.store_job_match(
                            subscription['device_id'],
                            job['id'],
                            matched_keywords,
                            relevance_score
                        )
                        
                        # Send push notification
                        await self.push_service.send_job_match_notification(
                            subscription['device_token'],
                            subscription['device_id'],
                            job,
                            matched_keywords,
                            match_id
                        )
                        
                        # Record metrics
                        metrics.record_match_created()
                        matches_created = True
                        
                        self.logger.info(
                            f"Match created: job {job['id']} -> device {subscription['device_id']} "
                            f"(score: {relevance_score:.2f})"
                        )
                        
            except Exception as e:
                self.logger.error(
                    f"Error processing job {job['id']} for subscription {subscription['id']}: {e}"
                )
        
        return matches_created
    
    async def match_already_exists(self, device_id: str, job_id: str) -> bool:
        """Check if a match already exists for this device+job combination"""
        try:
            query = """
                SELECT 1 FROM iosapp.job_matches 
                WHERE device_id = $1 AND job_id = $2 
                LIMIT 1
            """
            result = await db_manager.execute_query(query, device_id, str(job_id))
            return len(result) > 0 if result else False
            
        except Exception as e:
            self.logger.error(f"Error checking existing match: {e}")
            return False
    
    def check_location_filters(self, job: Dict[str, Any], location_filters: Optional[Dict]) -> bool:
        """Check if job matches location filters"""
        if not location_filters:
            return True
            
        # TODO: Implement location filtering logic
        # This would check job location against cities filter and remote_only flag
        # For now, return True (accept all jobs)
        return True
    
    def calculate_relevance(self, job: Dict[str, Any], matched_keywords: List[str], 
                          all_keywords: List[str]) -> float:
        """Calculate relevance score (0.0 to 1.0)"""
        # Base score: percentage of keywords matched
        base_score = len(matched_keywords) / len(all_keywords)
        
        # Bonus for title matches (more important than description matches)
        title = job.get('title', '').lower()
        title_matches = sum(1 for kw in matched_keywords if kw.lower() in title)
        title_bonus = (title_matches / len(matched_keywords)) * 0.3
        
        # Bonus for company name matches
        company = job.get('company', '').lower()
        company_matches = sum(1 for kw in matched_keywords if kw.lower() in company)
        company_bonus = (company_matches / len(matched_keywords)) * 0.1
        
        # Apply recency bonus based on created_at (posted_at doesn't exist)
        recency_bonus = 0.0
        if job.get('created_at'):
            job_created = job['created_at']
            # Use naive datetime comparison since database uses naive timestamps
            hours_old = (datetime.now() - job_created).total_seconds() / 3600
            if hours_old < 24:  # Jobs less than 24 hours old get bonus
                recency_bonus = (24 - hours_old) / 24 * 0.1
        
        total_score = base_score + title_bonus + company_bonus + recency_bonus
        return min(1.0, total_score)
    
    async def store_job_match(self, device_id: uuid.UUID, 
                            job_id: int, matched_keywords: List[str], 
                            relevance_score: float) -> str:
        """Store job match in database"""
        try:
            match_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO iosapp.job_matches 
                (id, device_id, job_id, matched_keywords, relevance_score)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await db_manager.execute_command(
                query,
                uuid.UUID(match_id),
                device_id,
                str(job_id),
                matched_keywords,
                str(relevance_score)
            )
            
            return match_id
            
        except Exception as e:
            self.logger.error(f"Error storing job match: {e}")
            raise e

class JobMatchScheduler:
    """Scheduler for running job matching at regular intervals"""
    
    def __init__(self, interval_minutes: int = 240):  # Changed to 4 hours (240 minutes) to align with scraper
        self.interval_minutes = interval_minutes
        self.match_engine = JobMatchEngine()
        self.running = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the job matching scheduler"""
        self.running = True
        self.logger.info(f"Starting job match scheduler (interval: {self.interval_minutes} minutes)")
        
        # Run once immediately on startup
        try:
            self.logger.info("Running initial job matching on startup...")
            await self.match_engine.process_new_jobs()
        except Exception as e:
            self.logger.error(f"Error in initial job matching: {e}")
        
        while self.running:
            try:
                self.logger.info(f"Waiting {self.interval_minutes} minutes until next matching run...")
                await asyncio.sleep(self.interval_minutes * 60)  # Convert to seconds
                
                self.logger.info("Running scheduled job matching...")
                await self.match_engine.process_new_jobs()
            except Exception as e:
                self.logger.error(f"Error in job match scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop(self):
        """Stop the job matching scheduler"""
        self.running = False
        self.logger.info("Job match scheduler stopped")

# Global scheduler instance
job_scheduler = JobMatchScheduler()