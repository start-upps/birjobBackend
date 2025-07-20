import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import json
import traceback

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
            
            # Use private key from environment variable first (preferred)
            if settings.APNS_PRIVATE_KEY:
                self.logger.info(f"Environment key length: {len(settings.APNS_PRIVATE_KEY)} chars")
                self.logger.info(f"Environment key starts with: {settings.APNS_PRIVATE_KEY[:30]}...")
                self.logger.info("Using APNs private key from environment variable")
                
                # Validate and fix PEM format of environment variable
                key_content = settings.APNS_PRIVATE_KEY.strip()
                
                # Remove extra quotes that might be added by environment variable parsing
                # Handle both single and double quotes, and nested quotes
                while ((key_content.startswith('"') and key_content.endswith('"')) or 
                       (key_content.startswith("'") and key_content.endswith("'"))):
                    key_content = key_content[1:-1].strip()
                    self.logger.info("Removed extra quotes from environment key")
                
                # Fix potential line break issues in environment variables
                if '\\n' in key_content:
                    key_content = key_content.replace('\\n', '\n')
                    self.logger.info("Fixed escaped newlines in environment key")
                
                if not key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                    self.logger.error("Environment APNs key is not in PEM format")
                    self.logger.error(f"Key starts with: {repr(key_content[:50])}")
                    # Continue to try file fallback
                else:
                    if not key_content.endswith('-----END PRIVATE KEY-----'):
                        self.logger.error("Environment APNs key is incomplete")
                        self.logger.error(f"Key ends with: {repr(key_content[-50:])}")
                        # Continue to try file fallback
                    else:
                        self.logger.info("Environment APNs key content verified and PEM format confirmed")
                        self.logger.info(f"Key content size: {len(key_content)} bytes")
                        
                        # Store config for lazy initialization (avoid event loop issues)
                        self._apns_config = {
                            'key_content': key_content,
                            'key_id': settings.APNS_KEY_ID,
                            'team_id': settings.APNS_TEAM_ID,
                            'topic': settings.APNS_BUNDLE_ID,
                            'use_sandbox': settings.APNS_SANDBOX,
                            'use_direct_key': True
                        }
                        self.apns_client = None
                        self.logger.info("APNs config prepared with environment key (lazy init)")
                        return
                
            # Check for production APNs key file as fallback
            production_key_path = "/etc/secrets/AuthKey_ZV2X5Y7D76.p8"
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
                    'key_id': 'ZV2X5Y7D76',  # Use correct key ID from filename
                    'team_id': settings.APNS_TEAM_ID,
                    'topic': settings.APNS_BUNDLE_ID,
                    'use_sandbox': settings.APNS_SANDBOX
                }
                self.apns_client = None  # Will be created on first use
                
                self.logger.info("APNs config prepared with production key file")
                return
            
            # Use private key from environment variable as fallback
            elif settings.APNS_PRIVATE_KEY:
                self.logger.info("Using APNs private key from environment variable")
                
                # Validate and fix PEM format of environment variable
                key_content = settings.APNS_PRIVATE_KEY.strip()
                
                # Remove extra quotes that might be added by environment variable parsing
                # Handle both single and double quotes, and nested quotes
                while ((key_content.startswith('"') and key_content.endswith('"')) or 
                       (key_content.startswith("'") and key_content.endswith("'"))):
                    key_content = key_content[1:-1].strip()
                    self.logger.info("Removed extra quotes from environment key")
                
                # Fix potential line break issues in environment variables
                if '\\n' in key_content:
                    key_content = key_content.replace('\\n', '\n')
                    self.logger.info("Fixed escaped newlines in environment key")
                
                if not key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                    self.logger.error("Environment APNs key is not in PEM format")
                    self.logger.error(f"Key starts with: {repr(key_content[:50])}")
                    return
                if not key_content.endswith('-----END PRIVATE KEY-----'):
                    self.logger.error("Environment APNs key is incomplete")
                    self.logger.error(f"Key ends with: {repr(key_content[-50:])}")
                    return
                
                self.logger.info("Environment APNs key content verified and PEM format confirmed")
                self.logger.info(f"Key content size: {len(key_content)} bytes")
                
                self._apns_config = {
                    'key_content': key_content,
                    'key_id': settings.APNS_KEY_ID,
                    'team_id': settings.APNS_TEAM_ID,
                    'topic': settings.APNS_BUNDLE_ID,
                    'use_sandbox': settings.APNS_SANDBOX,
                    'use_temp_file': True
                }
                self.apns_client = None
                self.logger.info("APNs config prepared with environment key")
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
            
            if self._apns_config.get('use_direct_key'):
                # Use key content directly with aioapns
                self.logger.info("Creating APNs client with direct key content")
                
                self.apns_client = APNs(
                    key=self._apns_config['key_content'],
                    key_id=self._apns_config['key_id'],
                    team_id=self._apns_config['team_id'],
                    topic=self._apns_config['topic'],
                    use_sandbox=self._apns_config['use_sandbox']
                )
                
                self.logger.info("APNs client created successfully with direct key")
                return self.apns_client
                
            elif self._apns_config.get('use_temp_file'):
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
    
    async def send_bulk_job_notifications(
        self,
        device_token: str,
        device_id: str,
        jobs: List[Dict[str, Any]],
        notification_ids: List[str]
    ) -> bool:
        """Send bulk job notifications to a user"""
        
        # Validate inputs
        if not device_token:
            self.logger.error(f"Cannot send bulk notification: device_token is None for device {device_id}")
            return False
        
        if not device_id:
            self.logger.error("Cannot send bulk notification: device_id is None")
            return False
        
        if not jobs:
            self.logger.debug("No jobs to send in bulk notification")
            return False
        
        # Check throttling
        if not await self._check_notification_throttling(device_id):
            self.logger.info(f"Bulk notification throttled for device {device_id}")
            return False
        
        # Check quiet hours
        if await self._is_quiet_hours(device_id):
            self.logger.info(f"Bulk notification suppressed (quiet hours) for device {device_id}")
            return False
        
        # Create bulk notification payload
        payload = self._create_bulk_job_payload(jobs, notification_ids)
        
        # Validate APNs configuration
        if not self._apns_config:
            self.logger.error("APNs configuration is not initialized")
            return False
        
        # Send notification (use 'job_match' type as 'bulk_job_match' is not in DB constraint)
        self.logger.info(f"Sending bulk notification to device {device_id} for {len(jobs)} jobs")
        self.logger.debug(f"Device token: {device_token[:20]}...")
        self.logger.debug(f"APNs config - Team ID: {self._apns_config.get('team_id')}, Bundle ID: {self._apns_config.get('topic')}, Sandbox: {self._apns_config.get('use_sandbox')}")
        success = await self._send_notification(device_token, payload, "job_match", notification_ids[0] if notification_ids else "bulk")
        
        if success:
            # Update notification counts
            await self._update_notification_counts(device_id)
            self.logger.info(f"Bulk notification sent successfully to device {device_id} for {len(jobs)} jobs")
        else:
            self.logger.warning(f"Failed to send bulk notification to device {device_id}")
        
        return success
    
    def _create_bulk_job_payload(
        self,
        jobs: List[Dict[str, Any]],
        notification_ids: List[str]
    ) -> Dict[str, Any]:
        """Create push notification payload for bulk job matches"""
        
        job_count = len(jobs)
        
        if job_count == 1:
            # Single job - use regular format
            job = jobs[0]['job_dict']
            matched_keywords = jobs[0]['matched_keywords']
            return self._create_job_match_payload(job, matched_keywords, notification_ids[0])
        
        # Multiple jobs - create summary
        companies = list(set([job['job_dict'].get('company', 'Unknown') for job in jobs[:5]]))
        company_count = len(companies)
        
        # Get unique keywords for custom_data
        all_keywords = []
        for job in jobs:
            all_keywords.extend(job['matched_keywords'])
        unique_keywords = list(set(all_keywords))
        
        # Create emoji variety for engagement
        job_emojis = ['💼', '🎯', '⭐', '🔥', '✨']
        company_emojis = ['🏢', '🏬', '🏭', '🏪', '🏦']
        
        # Use different emojis based on count to avoid repetition
        job_emoji = job_emojis[min(job_count-1, len(job_emojis)-1)]
        company_emoji = company_emojis[min(company_count-1, len(company_emojis)-1)]
        
        return {
            "aps": {
                "alert": {
                    "title": f"{job_emoji} {job_count} jobs",
                    "subtitle": f"{company_emoji} {company_count} companies",
                    "body": ""
                },
                "badge": job_count,
                "sound": "default",
                "category": "BULK_JOB_MATCH",
                "thread-id": "job-matches"
            },
            "custom_data": {
                "type": "bulk_job_match",
                "match_count": job_count,
                "notification_ids": notification_ids,
                "job_ids": [job['job_dict'].get('id') for job in jobs],
                "job_hashes": [job.get('job_hash', '') for job in jobs],  # Add hashes for persistence
                "job_data": [  # Store essential job data for offline access
                    {
                        "hash": job.get('job_hash', ''),
                        "title": job['job_dict'].get('title', ''),
                        "company": job['job_dict'].get('company', ''),
                        "apply_link": job['job_dict'].get('apply_link', '')
                    } for job in jobs[:5]  # Limit to 5 jobs to avoid payload size issues
                ],
                "matched_keywords": unique_keywords,
                "deep_link": "birjob://jobs/matches/bulk"
            }
        }
    
    def _create_job_match_payload(
        self,
        job: Dict[str, Any],
        matched_keywords: List[str],
        match_id: str
    ) -> Dict[str, Any]:
        """Create push notification payload for job match"""
        
        # Handle batch context for smart notifications
        batch_context = job.get('batch_context', {})
        total_matches = batch_context.get('total_matches', 1)
        
        # Truncate title and company for notification
        title = job.get('title', 'New Job')[:50]
        company = job.get('company', 'Unknown Company')[:30]
        keywords_text = ', '.join(matched_keywords[:3])  # Show max 3 keywords
        
        # Create smart notification text based on match count
        if total_matches > 1:
            notification_title = f"🎯 {title}"
            notification_subtitle = f"🏢 {company}"
            notification_body = f"💼 {keywords_text} • +{total_matches-1} more jobs"
        else:
            notification_title = f"🎯 {title}"
            notification_subtitle = f"🏢 {company}"
            notification_body = f"💼 {keywords_text}"
        
        return {
            "aps": {
                "alert": {
                    "title": notification_title,
                    "subtitle": notification_subtitle,
                    "body": notification_body
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
                "job_hash": match_id,  # Use hash for persistent reference
                "job_title": job.get('title', ''),
                "job_company": job.get('company', ''),
                "apply_link": job.get('apply_link', ''),  # Store direct apply link
                "matched_keywords": matched_keywords,
                "deep_link": f"birjob://job/hash/{match_id}"  # Hash-based deep link
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
        """Send push notification via APNs with comprehensive debugging"""
        
        notification_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        # Comprehensive pre-send logging
        self.logger.info(f"🔔 PUSH NOTIFICATION ATTEMPT [{notification_id}]")
        self.logger.info(f"   Device Token: {device_token[:20]}...{device_token[-10:]}")
        self.logger.info(f"   Type: {notification_type}")
        self.logger.info(f"   Match ID: {match_id}")
        self.logger.info(f"   Payload Size: {len(json.dumps(payload))} bytes")
        self.logger.info(f"   Timestamp: {start_time.isoformat()}")
        
        # Validate device token format
        if not self._validate_device_token(device_token):
            self.logger.error(f"❌ Invalid device token format: {device_token[:20]}...")
            return False
        
        # Skip NULL, empty, or temporary tokens
        if not device_token or device_token.startswith('temp_'):
            self.logger.warning(f"⚠️ Skipping notification - no valid token for device")
            self.logger.warning(f"   Device needs to register real APNs token via /notifications/token endpoint")
            return False
        
        # Validate payload size (APNs limit is 4KB)
        payload_size = len(json.dumps(payload))
        if payload_size > 4096:
            self.logger.error(f"❌ Payload too large: {payload_size} bytes (max 4096)")
            return False
        
        try:
            # NOTE: Notification storage is handled by minimal_notification_service.py
            # to avoid duplicates with job_source='push_notification'
            
            apns_client = await self._get_apns_client() if APNS_AVAILABLE else None
            if apns_client:
                # Log APNs configuration details
                self.logger.info(f"📡 APNs Configuration:")
                self.logger.info(f"   Team ID: {self._apns_config.get('team_id')}")
                self.logger.info(f"   Bundle ID: {self._apns_config.get('topic')}")
                self.logger.info(f"   Key ID: {self._apns_config.get('key_id')}")
                self.logger.info(f"   Sandbox: {self._apns_config.get('use_sandbox')}")
                self.logger.info(f"   Server: {'sandbox' if self._apns_config.get('use_sandbox') else 'production'}")
                
                # Send via APNs
                request = NotificationRequest(
                    device_token=device_token,
                    message=payload,
                    push_type=PushType.ALERT
                )
                
                self.logger.info(f"🚀 Sending to APNs...")
                response = await apns_client.send_notification(request)
                
                # Calculate processing time
                processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                # Detailed response logging
                self.logger.info(f"📥 APNs Response:")
                self.logger.info(f"   Status: {response.status}")
                self.logger.info(f"   Success: {response.is_successful}")
                self.logger.info(f"   Description: {response.description}")
                self.logger.info(f"   Processing Time: {processing_time:.3f}s")
                
                # Additional error context for BadDeviceToken
                if response.status == 400 and "BadDeviceToken" in response.description:
                    self.logger.error(f"🚨 BadDeviceToken Analysis:")
                    self.logger.error(f"   This is typically caused by:")
                    self.logger.error(f"   1. TestFlight app using production APNs (should use sandbox)")
                    self.logger.error(f"   2. Development app using production APNs")
                    self.logger.error(f"   3. Token from different bundle ID/certificate")
                    self.logger.error(f"   4. Expired or revoked token")
                    self.logger.error(f"   Current config: {'Production' if not self._apns_config.get('use_sandbox') else 'Sandbox'} APNs")
                    self.logger.error(f"   Recommendation: Verify app distribution method matches APNs environment")
                
                if hasattr(response, 'apns_id'):
                    self.logger.info(f"   APNs ID: {response.apns_id}")
                if hasattr(response, 'timestamp'):
                    self.logger.info(f"   Timestamp: {response.timestamp}")
                
                if response.is_successful:
                    response_data = {
                        "status": "success",
                        "apns_status": response.status,
                        "processing_time": processing_time,
                        "apns_id": getattr(response, 'apns_id', None)
                    }
                    await self._update_notification_status(notification_id, "sent", response_data)
                    self.logger.info(f"✅ Push notification sent successfully: {notification_id}")
                    return True
                else:
                    # Handle specific APNs errors
                    error_details = self._parse_apns_error(response)
                    response_data = {
                        "error": response.description,
                        "apns_status": response.status,
                        "processing_time": processing_time,
                        "error_details": error_details
                    }
                    await self._update_notification_status(notification_id, "failed", response_data)
                    self.logger.error(f"❌ Push notification failed: {response.description}")
                    self.logger.error(f"   Error Details: {error_details}")
                    return False
            else:
                # Mock mode for development
                self.logger.info(f"🧪 Mock push notification sent: {notification_id}")
                self.logger.info(f"   Would send to: {device_token[:20]}...")
                self.logger.info(f"   Payload: {json.dumps(payload, indent=2)}")
                await self._update_notification_status(notification_id, "sent", {"mock": True})
                return True
                
        except Exception as e:
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            error_details = {
                "error": str(e),
                "processing_time": processing_time,
                "traceback": self._get_error_traceback(e)
            }
            self.logger.error(f"💥 Error sending push notification: {e}")
            self.logger.error(f"   Processing Time: {processing_time:.3f}s")
            await self._update_notification_status(notification_id, "failed", error_details)
            return False
    
    
    async def _update_notification_status(
        self,
        notification_id: str,
        status: str,
        response: Any = None
    ):
        """Update notification status in database (using notification_hashes table)"""
        try:
            # Since we're using notification_hashes table, we don't need to update status
            # The notification is already tracked by its existence in the table
            # Just log the status for debugging
            self.logger.info(f"Notification {notification_id} status: {status}")
            
            if response:
                if hasattr(response, '__dict__'):
                    response_data = json.dumps(response.__dict__)
                else:
                    response_data = json.dumps(response)
                self.logger.info(f"APNs response: {response_data}")
            
            # No database update needed since we're using notification_hashes for tracking
            
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
        # TEMPORARY: Disable quiet hours for testing
        return False
        # return (current_hour >= settings.QUIET_HOURS_START or 
        #         current_hour < settings.QUIET_HOURS_END)
    
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
    
    def _validate_device_token(self, device_token: str) -> bool:
        """Validate APNs device token format with enhanced validation"""
        if not device_token:
            self.logger.error("Device token is empty")
            return False
        
        # APNs device tokens can be 64, 128, or 160 characters (hex)
        valid_lengths = [64, 128, 160]
        if len(device_token) not in valid_lengths:
            self.logger.error(f"Invalid token length: {len(device_token)} (expected 64, 128, or 160)")
            return False
        
        # Should only contain hex characters
        try:
            int(device_token, 16)
        except ValueError:
            self.logger.error(f"Invalid token format: contains non-hex characters")
            return False
        
        # Check for repeating patterns (common in simulator/test tokens)
        # APNs rejects tokens with too much repetition
        if self._has_repeating_pattern(device_token):
            self.logger.warning(f"Device token has repeating patterns - likely iOS Simulator token")
            self.logger.warning(f"APNs will reject this token. Use a real device for testing.")
            return False
            
        return True
    
    def _has_repeating_pattern(self, token: str) -> bool:
        """Check if token has excessive repeating patterns (common in simulator tokens)"""
        # Check for excessive repetition of small patterns
        for pattern_length in [2, 4, 8]:
            for i in range(0, len(token) - pattern_length + 1, pattern_length):
                pattern = token[i:i + pattern_length]
                repetitions = 0
                
                # Count consecutive repetitions
                for j in range(i + pattern_length, len(token), pattern_length):
                    if j + pattern_length <= len(token) and token[j:j + pattern_length] == pattern:
                        repetitions += 1
                    else:
                        break
                
                # If we find 4+ consecutive repetitions of the same pattern, it's likely a test token
                if repetitions >= 4:
                    return True
        
        return False
    
    def _parse_apns_error(self, response) -> Dict[str, Any]:
        """Parse APNs error response for detailed debugging"""
        error_details = {
            "status_code": response.status,
            "description": response.description,
            "recommendations": []
        }
        
        # Map common APNs errors to actionable recommendations
        error_map = {
            400: {
                "BadDeviceToken": "Device token is malformed or invalid",
                "BadExpirationDate": "Expiration date is invalid",
                "BadMessageId": "Message ID is invalid",
                "BadPriority": "Priority value is invalid",
                "BadTopic": "Topic/Bundle ID is invalid or doesn't match certificate",
                "DeviceTokenNotForTopic": "Device token doesn't match the topic",
                "DuplicateHeaders": "Duplicate headers in request",
                "IdleTimeout": "Connection was idle too long",
                "MissingDeviceToken": "Device token is missing",
                "MissingTopic": "Topic is missing",
                "PayloadEmpty": "Payload is empty",
                "TopicDisallowed": "Topic is not allowed"
            },
            403: {
                "BadCertificate": "Certificate is invalid",
                "BadCertificateEnvironment": "Certificate environment mismatch",
                "ExpiredProviderToken": "Provider token is expired",
                "Forbidden": "Request is forbidden",
                "InvalidProviderToken": "Provider token is invalid",
                "MissingProviderToken": "Provider token is missing"
            },
            404: {
                "BadPath": "Request path is invalid"
            },
            405: {
                "MethodNotAllowed": "HTTP method not allowed"
            },
            410: {
                "Unregistered": "Device token is no longer valid"
            },
            413: {
                "PayloadTooLarge": "Payload exceeds 4KB limit"
            },
            429: {
                "TooManyRequests": "Too many requests sent to APNs"
            },
            500: {
                "InternalServerError": "APNs internal server error"
            },
            503: {
                "ServiceUnavailable": "APNs service unavailable"
            }
        }
        
        status_errors = error_map.get(response.status, {})
        
        # Add specific recommendations based on error
        if response.status == 400:
            if "BadTopic" in response.description:
                error_details["recommendations"].append("Check that Bundle ID matches your app's bundle identifier")
                error_details["recommendations"].append("Verify APNs certificate/key is for the correct app")
            elif "BadDeviceToken" in response.description:
                error_details["recommendations"].append("Verify device token format (64 hex characters)")
                error_details["recommendations"].append("Check that device token is from the correct environment")
        elif response.status == 403:
            error_details["recommendations"].append("Check APNs certificate/key validity")
            error_details["recommendations"].append("Verify Team ID and Key ID are correct")
            error_details["recommendations"].append("Ensure using correct environment (sandbox vs production)")
        elif response.status == 410:
            error_details["recommendations"].append("Device token is no longer valid - remove from database")
            error_details["recommendations"].append("App may have been uninstalled or token refreshed")
        
        return error_details
    
    def _get_error_traceback(self, error: Exception) -> str:
        """Get formatted error traceback for debugging"""
        import traceback
        return traceback.format_exc()
    
    async def validate_device_token_with_apns(self, device_token: str) -> Dict[str, Any]:
        """Validate device token by sending a test notification to APNs"""
        validation_result = {
            "device_token": device_token[:20] + "..." + device_token[-10:],
            "valid": False,
            "error": None,
            "recommendations": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Basic format validation
            if not self._validate_device_token(device_token):
                validation_result["error"] = "Invalid device token format"
                validation_result["recommendations"].append("Ensure token is 64 hex characters")
                return validation_result
            
            # Test with minimal payload
            test_payload = {
                "aps": {
                    "alert": {
                        "title": "Connection Test",
                        "body": "Testing APNs connection"
                    },
                    "badge": 0,
                    "sound": "default"
                }
            }
            
            apns_client = await self._get_apns_client() if APNS_AVAILABLE else None
            if not apns_client:
                validation_result["error"] = "APNs client not available"
                validation_result["recommendations"].append("Check APNs configuration")
                return validation_result
            
            request = NotificationRequest(
                device_token=device_token,
                message=test_payload,
                push_type=PushType.ALERT
            )
            
            response = await apns_client.send_notification(request)
            
            if response.is_successful:
                validation_result["valid"] = True
                validation_result["apns_id"] = getattr(response, 'apns_id', None)
            else:
                validation_result["error"] = response.description
                validation_result["apns_status"] = response.status
                validation_result["error_details"] = self._parse_apns_error(response)
                validation_result["recommendations"] = validation_result["error_details"]["recommendations"]
            
            return validation_result
            
        except Exception as e:
            validation_result["error"] = str(e)
            validation_result["recommendations"].append("Check APNs configuration and network connectivity")
            return validation_result
    
    async def get_apns_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive APNs configuration diagnostics"""
        diagnostics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "apns_available": APNS_AVAILABLE,
            "client_initialized": self.apns_client is not None,
            "configuration": {},
            "environment": {},
            "validation": {}
        }
        
        if self._apns_config:
            diagnostics["configuration"] = {
                "team_id": self._apns_config.get('team_id'),
                "key_id": self._apns_config.get('key_id'),
                "bundle_id": self._apns_config.get('topic'),
                "sandbox": self._apns_config.get('use_sandbox'),
                "server": 'sandbox' if self._apns_config.get('use_sandbox') else 'production',
                "key_source": "environment" if self._apns_config.get('use_direct_key') else "file",
                "key_path": self._apns_config.get('key') if not self._apns_config.get('use_direct_key') else None
            }
        
        # Environment validation
        import os
        diagnostics["environment"] = {
            "has_private_key_env": bool(settings.APNS_PRIVATE_KEY),
            "key_file_exists": os.path.exists(settings.APNS_KEY_PATH),
            "production_key_exists": os.path.exists("/etc/secrets/AuthKey_ZV2X5Y7D76.p8"),
            "settings_valid": all([
                settings.APNS_TEAM_ID,
                settings.APNS_KEY_ID,
                settings.APNS_BUNDLE_ID
            ])
        }
        
        # Validation checks
        diagnostics["validation"] = {
            "config_complete": bool(self._apns_config),
            "required_fields": {
                "team_id": bool(self._apns_config and self._apns_config.get('team_id')),
                "key_id": bool(self._apns_config and self._apns_config.get('key_id')),
                "bundle_id": bool(self._apns_config and self._apns_config.get('topic')),
                "key_available": bool(self._apns_config and (
                    self._apns_config.get('key_content') or 
                    self._apns_config.get('key')
                ))
            }
        }
        
        return diagnostics