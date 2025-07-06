import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import json

try:
    from aioapns import APNs, NotificationRequest, PushType
    APNS_AVAILABLE = True
except ImportError:
    APNS_AVAILABLE = False
    logging.warning("aioapns not available - push notifications will be mocked")

from app.core.config import settings
from app.core.database import db_manager
from app.core.redis_client import redis_client
# Removed monitoring dependency

logger = logging.getLogger(__name__)

class PushNotificationService:
    """Service for sending Apple Push Notifications"""
    
    def __init__(self):
        self.apns_client = None
        self._apns_config = None
        self.logger = logging.getLogger(__name__)
        
        if APNS_AVAILABLE:
            self._init_apns_client()
    
    def _init_apns_client(self):
        """Initialize APNs client"""
        try:
            import os
            
            # Debug logging
            self.logger.info(f"APNS_PRIVATE_KEY present: {bool(settings.APNS_PRIVATE_KEY)}")
            self.logger.info(f"APNS_KEY_PATH: {settings.APNS_KEY_PATH}")
            self.logger.info(f"APNS_KEY_ID: {settings.APNS_KEY_ID}")
            self.logger.info(f"APNS_TEAM_ID: {settings.APNS_TEAM_ID}")
            self.logger.info(f"APNS_BUNDLE_ID: {settings.APNS_BUNDLE_ID}")
            
            # Use private key from environment variable if available (preferred)
            if settings.APNS_PRIVATE_KEY:
                self.logger.info("Using APNs private key from environment variable")
                
                # Validate PEM format of environment variable
                key_content = settings.APNS_PRIVATE_KEY.strip()
                if not key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                    self.logger.error("Environment APNs key is not in PEM format")
                    self.logger.error(f"Key starts with: {key_content[:50]}...")
                    return
                if not key_content.endswith('-----END PRIVATE KEY-----'):
                    self.logger.error("Environment APNs key is incomplete")
                    return
                
                self.logger.info("Environment APNs key content verified and PEM format confirmed")
                self.logger.info(f"Key content size: {len(key_content)} bytes")
                
                self._apns_config = {
                    'key_content': settings.APNS_PRIVATE_KEY,
                    'key_id': settings.APNS_KEY_ID,
                    'team_id': settings.APNS_TEAM_ID,
                    'topic': settings.APNS_BUNDLE_ID,
                    'use_sandbox': settings.APNS_SANDBOX,
                    'use_temp_file': True
                }
                self.apns_client = None
                self.logger.info("APNs config prepared with environment key")
                return
                
            # Check for production APNs key file as fallback
            production_key_path = "/etc/secrets/apn.p8"
            if os.path.exists(production_key_path):
                self.logger.info(f"Using production APNs key from: {production_key_path}")
                
                try:
                    with open(production_key_path, 'r') as f:
                        key_content = f.read()
                        if key_content.strip():
                            # Validate PEM format
                            if not key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                                self.logger.error("Production APNs key file is not in PEM format")
                                self.logger.error(f"Key starts with: {key_content[:50]}...")
                                return
                            if not key_content.strip().endswith('-----END PRIVATE KEY-----'):
                                self.logger.error("Production APNs key file is incomplete")
                                return
                            self.logger.info("Production APNs key content verified and PEM format confirmed")
                            self.logger.info(f"Key file size: {len(key_content)} bytes")
                        else:
                            self.logger.error("Production APNs key file is empty")
                            return
                except Exception as e:
                    self.logger.error(f"Cannot read production APNs key file: {e}")
                    return
                
                # Initialize APNs client with production key - lazy initialization
                self._apns_config = {
                    'key': production_key_path,
                    'key_id': settings.APNS_KEY_ID,
                    'team_id': settings.APNS_TEAM_ID,
                    'topic': settings.APNS_BUNDLE_ID,
                    'use_sandbox': settings.APNS_SANDBOX
                }
                self.apns_client = None  # Will be created on first use
                
                self.logger.info("APNs config prepared with production key file")
                return
                
            # Check if key file exists
            elif os.path.exists(settings.APNS_KEY_PATH):
                self.logger.info(f"APNs key file found at: {settings.APNS_KEY_PATH}")
                
                # Verify the file is readable and not empty
                try:
                    with open(settings.APNS_KEY_PATH, 'r') as f:
                        key_content = f.read()
                        if key_content.strip():
                            self.logger.info("APNs key file content verified")
                        else:
                            self.logger.error("APNs key file is empty")
                            return
                except Exception as e:
                    self.logger.error(f"Cannot read APNs key file: {e}")
                    return
                
                # Store config for lazy initialization
                self._apns_config = {
                    'key': settings.APNS_KEY_PATH,
                    'key_id': settings.APNS_KEY_ID,
                    'team_id': settings.APNS_TEAM_ID,
                    'topic': settings.APNS_BUNDLE_ID,
                    'use_sandbox': settings.APNS_SANDBOX
                }
                self.apns_client = None
                self.logger.info("APNs config prepared with key file")
                
            else:
                self.logger.error(f"APNs key file not found: {settings.APNS_KEY_PATH}")
                
                # List files in /etc/secrets to debug
                secrets_dir = "/etc/secrets"
                if os.path.exists(secrets_dir):
                    files = os.listdir(secrets_dir)
                    self.logger.info(f"Files in {secrets_dir}: {files}")
                else:
                    self.logger.error(f"Directory {secrets_dir} does not exist")
                
                return
            
        except Exception as e:
            self.logger.error(f"Failed to initialize APNs client: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self.apns_client = None
    
    async def _get_apns_client(self):
        """Get APNs client with lazy initialization"""
        if self.apns_client is not None:
            return self.apns_client
            
        if not self._apns_config:
            self.logger.error("No APNs configuration available")
            return None
            
        try:
            import os
            import tempfile
            
            if self._apns_config.get('use_temp_file'):
                # Create temporary file for environment key
                with tempfile.NamedTemporaryFile(mode='w', suffix='.p8', delete=False) as f:
                    f.write(self._apns_config['key_content'])
                    temp_key_path = f.name
                
                self.apns_client = APNs(
                    key=temp_key_path,
                    key_id=self._apns_config['key_id'],
                    team_id=self._apns_config['team_id'],
                    topic=self._apns_config['topic'],
                    use_sandbox=self._apns_config['use_sandbox']
                )
                
                # Clean up temporary file
                os.unlink(temp_key_path)
            else:
                # Use key file path - validate file exists and is readable
                key_path = self._apns_config['key']
                if not os.path.exists(key_path):
                    raise Exception(f"APNs key file not found: {key_path}")
                
                # Read and validate key content
                with open(key_path, 'r') as f:
                    key_content = f.read()
                    if not key_content.strip():
                        raise Exception("APNs key file is empty")
                    if not key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                        raise Exception("APNs key file is not in proper PEM format")
                    if not key_content.strip().endswith('-----END PRIVATE KEY-----'):
                        raise Exception("APNs key file is incomplete or corrupted")
                
                self.logger.info(f"Creating APNs client with key file: {key_path}")
                self.apns_client = APNs(
                    key=key_path,
                    key_id=self._apns_config['key_id'],
                    team_id=self._apns_config['team_id'],
                    topic=self._apns_config['topic'],
                    use_sandbox=self._apns_config['use_sandbox']
                )
            
            self.logger.info("APNs client created successfully")
            return self.apns_client
            
        except Exception as e:
            self.logger.error(f"Failed to create APNs client: {e}")
            return None
    
    async def send_job_match_notification(
        self,
        device_token: str,
        device_id: str,
        job: Dict[str, Any],
        matched_keywords: List[str],
        match_id: str
    ) -> bool:
        """Send job match push notification"""
        
        # Check throttling
        if not await self._check_notification_throttling(device_id):
            self.logger.info(f"Notification throttled for device {device_id}")
            return False
        
        # Check quiet hours
        if await self._is_quiet_hours(device_id):
            self.logger.info(f"Notification suppressed (quiet hours) for device {device_id}")
            # Store notification for later delivery
            await self._store_pending_notification(device_token, device_id, job, matched_keywords, match_id)
            return False
        
        # Create notification payload
        payload = self._create_job_match_payload(job, matched_keywords, match_id)
        
        # Send notification
        success = await self._send_notification(device_token, payload, "job_match", match_id)
        
        if success:
            # Update notification counts
            await self._update_notification_counts(device_id)
            logger.info(f"Notification sent successfully to device {device_id}")
        else:
            logger.warning(f"Failed to send notification to device {device_id}")
        
        return success
    
    def _create_job_match_payload(
        self,
        job: Dict[str, Any],
        matched_keywords: List[str],
        match_id: str
    ) -> Dict[str, Any]:
        """Create push notification payload for job match"""
        
        # Truncate title and company for notification
        title = job.get('title', 'New Job')[:50]
        company = job.get('company', 'Unknown Company')[:30]
        keywords_text = ', '.join(matched_keywords[:3])  # Show max 3 keywords
        
        return {
            "aps": {
                "alert": {
                    "title": "New Job Match! 🎯",
                    "subtitle": f"{title} at {company}",
                    "body": f"Matches your keywords: {keywords_text}"
                },
                "badge": 1,
                "sound": "default",
                "category": "JOB_MATCH",
                "thread-id": "job-matches"
            },
            "custom_data": {
                "type": "job_match",
                "match_id": match_id,
                "job_id": job.get('id'),
                "matched_keywords": matched_keywords,
                "deep_link": f"birjob://job/{job.get('id')}"
            }
        }
    
    async def send_daily_digest(self, device_token: str, device_id: str, matches_count: int) -> bool:
        """Send daily digest notification"""
        if matches_count == 0:
            return True  # No notification needed
        
        payload = {
            "aps": {
                "alert": {
                    "title": "Daily Job Summary 📊",
                    "body": f"You have {matches_count} new job matches today"
                },
                "badge": matches_count,
                "sound": "default",
                "category": "DAILY_DIGEST"
            },
            "custom_data": {
                "type": "daily_digest",
                "matches_count": matches_count,
                "deep_link": "birjob://matches"
            }
        }
        
        return await self._send_notification(device_token, payload, "daily_digest")
    
    async def send_system_notification(
        self,
        device_token: str,
        device_id: str,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ) -> bool:
        """Send system notification"""
        payload = {
            "aps": {
                "alert": {
                    "title": title,
                    "body": message
                },
                "sound": "default",
                "category": "SYSTEM"
            },
            "custom_data": {
                "type": "system",
                **(data or {})
            }
        }
        
        return await self._send_notification(device_token, payload, "system")
    
    async def _send_notification(
        self,
        device_token: str,
        payload: Dict[str, Any],
        notification_type: str,
        match_id: Optional[str] = None
    ) -> bool:
        """Send push notification via APNs"""
        
        notification_id = str(uuid.uuid4())
        
        try:
            # Store notification in database first
            await self._store_notification(
                device_token, notification_id, payload, notification_type, match_id
            )
            
            apns_client = await self._get_apns_client() if APNS_AVAILABLE else None
            if apns_client:
                # Send via APNs
                request = NotificationRequest(
                    device_token=device_token,
                    message=payload,
                    push_type=PushType.ALERT
                )
                
                response = await apns_client.send_notification(request)
                
                if response.is_successful:
                    await self._update_notification_status(notification_id, "sent", response)
                    self.logger.info(f"Push notification sent successfully: {notification_id}")
                    return True
                else:
                    await self._update_notification_status(notification_id, "failed", response)
                    self.logger.error(f"Push notification failed: {response.description}")
                    return False
            else:
                # Mock mode for development
                self.logger.info(f"Mock push notification sent: {notification_id}")
                await self._update_notification_status(notification_id, "sent", {"mock": True})
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending push notification: {e}")
            await self._update_notification_status(notification_id, "failed", {"error": str(e)})
            return False
    
    async def _store_notification(
        self,
        device_token: str,
        notification_id: str,
        payload: Dict[str, Any],
        notification_type: str,
        match_id: Optional[str] = None
    ):
        """Store notification in database"""
        try:
            # Get device info from token
            device_query = """
                SELECT dt.id as device_id, dt.user_id 
                FROM iosapp.device_tokens dt 
                WHERE dt.device_token = $1
            """
            device_result = await db_manager.execute_query(device_query, device_token)
            
            if not device_result:
                raise Exception(f"Device not found for token: {device_token}")
            
            device_data = device_result[0]
            
            # Handle both old and new schema - check if job_notification_id exists, otherwise use match_id
            try:
                # Try with new schema (job_notification_id)
                query = """
                    INSERT INTO iosapp.push_notifications 
                    (id, device_id, user_id, job_notification_id, notification_type, payload, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                
                await db_manager.execute_command(
                    query,
                    uuid.UUID(notification_id),
                    device_data['device_id'],
                    device_data['user_id'],
                    uuid.UUID(match_id) if match_id else None,
                    notification_type,
                    json.dumps(payload),
                    "pending"
                )
                
            except Exception as schema_error:
                # If that fails, try with old schema (match_id)
                if "job_notification_id" in str(schema_error):
                    self.logger.info("Falling back to old schema with match_id column")
                    query = """
                        INSERT INTO iosapp.push_notifications 
                        (id, device_id, user_id, match_id, notification_type, payload, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """
                    
                    await db_manager.execute_command(
                        query,
                        uuid.UUID(notification_id),
                        device_data['device_id'],
                        device_data['user_id'],
                        uuid.UUID(match_id) if match_id else None,
                        notification_type,
                        json.dumps(payload),
                        "pending"
                    )
                else:
                    # If it's a different error, re-raise it
                    raise schema_error
            
        except Exception as e:
            self.logger.error(f"Error storing notification: {e}")
            raise e
    
    async def _update_notification_status(
        self,
        notification_id: str,
        status: str,
        response: Any = None
    ):
        """Update notification status in database"""
        try:
            query = """
                UPDATE iosapp.push_notifications 
                SET status = $1, apns_response = $2, sent_at = NOW()
                WHERE id = $3
            """
            
            response_data = None
            if response:
                if hasattr(response, '__dict__'):
                    response_data = json.dumps(response.__dict__)
                else:
                    response_data = json.dumps(response)
            
            await db_manager.execute_command(
                query,
                status,
                response_data,
                uuid.UUID(notification_id)
            )
            
        except Exception as e:
            self.logger.error(f"Error updating notification status: {e}")
    
    async def _check_notification_throttling(self, device_id: str) -> bool:
        """Check if device has exceeded notification limits"""
        
        # Check hourly limit
        hour_count = await redis_client.get_notification_count(device_id, "hour")
        if hour_count >= settings.MAX_NOTIFICATIONS_PER_HOUR:
            return False
        
        # Check daily limit
        day_count = await redis_client.get_notification_count(device_id, "day")
        if day_count >= settings.MAX_NOTIFICATIONS_PER_DAY:
            return False
        
        return True
    
    async def _update_notification_counts(self, device_id: str):
        """Update notification counts in Redis"""
        # Increment hourly count (expires after 1 hour)
        await redis_client.increment_notification_count(device_id, "hour", 3600)
        
        # Increment daily count (expires after 24 hours)
        await redis_client.increment_notification_count(device_id, "day", 86400)
    
    async def _is_quiet_hours(self, device_id: str) -> bool:
        """Check if it's quiet hours for device based on timezone"""
        # TODO: Implement timezone-aware quiet hours check
        # For now, use UTC time
        current_hour = datetime.now(timezone.utc).hour
        return (current_hour >= settings.QUIET_HOURS_START or 
                current_hour < settings.QUIET_HOURS_END)
    
    async def _store_pending_notification(
        self,
        device_token: str,
        device_id: str,
        job: Dict[str, Any],
        matched_keywords: List[str],
        match_id: str
    ):
        """Store notification for later delivery (during quiet hours)"""
        # TODO: Implement pending notification storage
        # This would store notifications to be sent when quiet hours end
        pass