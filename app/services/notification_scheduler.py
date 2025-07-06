import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services.job_notification_service import job_notification_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Scheduler for automatic job notifications"""
    
    def __init__(self):
        self.running = False
        self.task = None
        self.logger = logging.getLogger(__name__)
    
    async def start_scheduler(self):
        """Start the notification scheduler"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
        self.logger.info("Notification scheduler started")
    
    async def stop_scheduler(self):
        """Stop the notification scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Notification scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check if it's time to run notifications
                if self._should_run_notifications():
                    self.logger.info("Running scheduled job notifications...")
                    
                    # Process notifications in LIVE mode (no dry run)
                    stats = await job_notification_service.process_job_notifications(
                        limit=getattr(settings, 'NOTIFICATION_BATCH_SIZE', 200),
                        dry_run=False
                    )
                    
                    self.logger.info(f"Scheduled notifications completed: {stats}")
                    
                    # Cleanup old notifications weekly
                    if self._should_cleanup_notifications():
                        self.logger.info("Running notification cleanup...")
                        deleted_count = await job_notification_service.cleanup_old_notifications(
                            days_old=getattr(settings, 'NOTIFICATION_CLEANUP_DAYS', 30)
                        )
                        self.logger.info(f"Cleaned up {deleted_count} old notification records")
                
                # Wait for next check (every 5 minutes)
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in notification scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def _should_run_notifications(self) -> bool:
        """Check if notifications should be run now"""
        now = datetime.now()
        
        # Run every hour between 8 AM and 10 PM
        if now.hour < 8 or now.hour > 22:
            return False
        
        # Run at specific minutes (e.g., :05, :35 past each hour)
        if now.minute in [5, 35]:
            return True
        
        return False
    
    def _should_cleanup_notifications(self) -> bool:
        """Check if notification cleanup should be run"""
        now = datetime.now()
        
        # Run cleanup on Sundays at 3 AM
        if now.weekday() == 6 and now.hour == 3 and now.minute < 5:
            return True
        
        return False

# Global scheduler instance
notification_scheduler = NotificationScheduler()

# For manual testing
async def run_notifications_now(dry_run: bool = False) -> dict:
    """Run notifications immediately (for testing) - LIVE MODE by default"""
    return await job_notification_service.process_job_notifications(
        limit=100,
        dry_run=dry_run
    )