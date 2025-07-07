from fastapi import APIRouter, HTTPException
from app.services.push_notifications import PushNotificationService
from app.core.database import db_manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/send-test-notification/{device_id}")
async def send_test_notification(device_id: str):
    """Send a test notification with detailed logging"""
    
    try:
        # Get device info
        device_query = """
            SELECT dt.device_token, dt.user_id, u.keywords 
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            return {"error": "Device not found", "device_id": device_id}
        
        device_data = device_result[0]
        device_token = device_data['device_token']
        
        result = {
            "device_id": device_id,
            "device_token": device_token,
            "device_token_length": len(device_token),
            "user_id": str(device_data['user_id']),
            "keywords": device_data['keywords']
        }
        
        # Check if device token looks like a real APNs token
        if len(device_token) == 64 and all(c in '0123456789abcdefABCDEF' for c in device_token):
            result["device_token_format"] = "Valid hex format"
        else:
            result["device_token_format"] = "Invalid - not hex or wrong length"
            
        # Create push service and test
        push_service = PushNotificationService()
        
        # Test APNs client creation
        if hasattr(push_service, 'apns_client') and push_service.apns_client:
            result["apns_client_status"] = "Already created"
        else:
            apns_client = await push_service._get_apns_client()
            if apns_client:
                result["apns_client_status"] = "Created successfully"
            else:
                result["apns_client_status"] = "Failed to create"
                return result
        
        # Try to send a test notification
        test_job = {
            "id": "test-debug-001",
            "title": "🔔 APNs Debug Test",
            "company": "Notification System",
            "apply_link": "https://example.com"
        }
        
        success = await push_service.send_job_match_notification(
            device_token=device_token,
            device_id=device_id,
            job=test_job,
            matched_keywords=["Debug", "Test"],
            match_id="debug-test-001"
        )
        
        result["notification_sent"] = success
        result["message"] = "Test notification attempted"
        
        return result
        
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return {"error": str(e), "device_id": device_id}