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
        """Main matching engine - processes jobs from last interval"""
        try:
            # Get jobs from last 10 minutes (with overlap buffer)
            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
            
            new_jobs = await self.get_new_jobs_since(cutoff_time)
            if not new_jobs:
                self.logger.info("No new jobs to process")
                return
            
            self.logger.info(f"Processing {len(new_jobs)} new jobs")
            
            # Get all active subscriptions with caching
            active_subscriptions = await self.get_active_subscriptions()
            
            if not active_subscriptions:
                self.logger.info("No active subscriptions found")
                return
            
            for job in new_jobs:
                await self.match_job_to_subscriptions(job, active_subscriptions)
                
        except Exception as e:
            self.logger.error(f"Error in match engine: {e}", exc_info=True)
    
    async def get_new_jobs_since(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get new jobs from scraper schema since cutoff time"""
        try:
            query = """
                SELECT id, title, company, apply_link, source, posted_at, created_at, description
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
    
    async def match_job_to_subscriptions(self, job: Dict[str, Any], subscriptions: List[Dict[str, Any]]):
        """Match a single job against all active subscriptions"""
        job_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')}".lower()
        
        for subscription in subscriptions:
            try:
                # Check if this job was already processed for this device
                if await redis_client.is_job_processed(str(subscription['device_id']), job['id']):
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
                    if relevance_score >= 0.3:  # Configurable threshold
                        # Store match in database
                        match_id = await self.store_job_match(
                            subscription['device_id'],
                            subscription['id'],
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
                        
                        # Mark as processed
                        await redis_client.mark_job_processed(
                            str(subscription['device_id']), 
                            job['id']
                        )
                        
                        # Record metrics
                        metrics.record_match_created()
                        
                        self.logger.info(
                            f"Match created: job {job['id']} -> device {subscription['device_id']} "
                            f"(score: {relevance_score:.2f})"
                        )
                        
            except Exception as e:
                self.logger.error(
                    f"Error processing job {job['id']} for subscription {subscription['id']}: {e}"
                )
    
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
        
        # Apply recency bonus (newer jobs get higher scores)
        recency_bonus = 0.0
        if job.get('posted_at'):
            hours_old = (datetime.utcnow() - job['posted_at']).total_seconds() / 3600
            if hours_old < 24:  # Jobs less than 24 hours old get bonus
                recency_bonus = (24 - hours_old) / 24 * 0.1
        
        total_score = base_score + title_bonus + company_bonus + recency_bonus
        return min(1.0, total_score)
    
    async def store_job_match(self, device_id: uuid.UUID, subscription_id: uuid.UUID, 
                            job_id: int, matched_keywords: List[str], 
                            relevance_score: float) -> str:
        """Store job match in database"""
        try:
            match_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO iosapp.job_matches 
                (id, device_id, subscription_id, job_id, matched_keywords, relevance_score)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            
            await db_manager.execute_command(
                query,
                uuid.UUID(match_id),
                device_id,
                subscription_id,
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
    
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.match_engine = JobMatchEngine()
        self.running = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the job matching scheduler"""
        self.running = True
        self.logger.info(f"Starting job match scheduler (interval: {self.interval_minutes} minutes)")
        
        while self.running:
            try:
                await self.match_engine.process_new_jobs()
                await asyncio.sleep(self.interval_minutes * 60)  # Convert to seconds
            except Exception as e:
                self.logger.error(f"Error in job match scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop(self):
        """Stop the job matching scheduler"""
        self.running = False
        self.logger.info("Job match scheduler stopped")

# Global scheduler instance
job_scheduler = JobMatchScheduler()