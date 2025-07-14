"""
Privacy management endpoints for GDPR/CCPA compliance
Allows users to manage their analytics consent and data
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
from pydantic import BaseModel

from app.core.database import db_manager
from app.utils.validation import validate_device_token
from app.services.privacy_analytics_service import privacy_analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class AnalyticsConsentRequest(BaseModel):
    device_token: str
    consent: bool
    privacy_policy_version: str = "1.0"

class DataExportRequest(BaseModel):
    device_token: str
    email: Optional[str] = None  # Optional email for sending export

@router.get("/status/{device_token}")
async def get_privacy_status(device_token: str):
    """Get user's current privacy and consent status"""
    try:
        device_token = validate_device_token(device_token)
        
        # Get device and privacy info
        query = """
            SELECT id, analytics_consent, consent_date, privacy_policy_version, 
                   notifications_enabled, created_at
            FROM iosapp.device_users 
            WHERE device_token = $1
        """
        result = await db_manager.execute_query(query, device_token)
        
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device = result[0]
        
        # Get analytics data count if user has consented
        analytics_count = 0
        if device['analytics_consent']:
            count_query = """
                SELECT COUNT(*) as count 
                FROM iosapp.user_analytics 
                WHERE device_id = $1
            """
            count_result = await db_manager.execute_query(count_query, device['id'])
            analytics_count = count_result[0]['count'] if count_result else 0
        
        return {
            "success": True,
            "data": {
                "device_id": str(device['id']),
                "device_token_preview": device_token[:16] + "...",
                "privacy_status": {
                    "analytics_consent": device['analytics_consent'],
                    "consent_date": device['consent_date'].isoformat() if device['consent_date'] else None,
                    "privacy_policy_version": device['privacy_policy_version'],
                    "notifications_enabled": device['notifications_enabled']
                },
                "data_summary": {
                    "analytics_events_stored": analytics_count,
                    "registration_date": device['created_at'].isoformat(),
                    "data_retention_note": "Analytics data is retained while consent is active"
                },
                "your_rights": {
                    "consent": "You can grant or revoke analytics consent at any time",
                    "access": "You can request a copy of your data",
                    "deletion": "You can request deletion of your data",
                    "portability": "You can export your data in JSON format"
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting privacy status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get privacy status")

@router.post("/consent")
async def set_analytics_consent(request: AnalyticsConsentRequest):
    """Set or update user's analytics consent (GDPR compliance)"""
    try:
        device_token = validate_device_token(request.device_token)
        
        # Get device ID
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Set consent using privacy service
        success = await privacy_analytics_service.set_analytics_consent(
            device_id, 
            request.consent, 
            request.privacy_policy_version
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update consent")
        
        action = "granted" if request.consent else "revoked"
        data_action = "" if request.consent else " and existing data deleted"
        
        return {
            "success": True,
            "message": f"Analytics consent {action} successfully{data_action}",
            "data": {
                "analytics_consent": request.consent,
                "privacy_policy_version": request.privacy_policy_version,
                "consent_date": datetime.now(timezone.utc).isoformat(),
                "data_retention": "Data will be collected and stored" if request.consent else "No data will be collected",
                "rights_note": "You can change this setting at any time"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting analytics consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to set analytics consent")

@router.delete("/data/{device_token}")
async def delete_user_data(device_token: str):
    """Delete all analytics data for user (GDPR right to be forgotten)"""
    try:
        device_token = validate_device_token(device_token)
        
        # Get device ID
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Delete analytics data
        deleted_count = await privacy_analytics_service.delete_analytics_data(device_id)
        
        # Revoke consent
        await privacy_analytics_service.set_analytics_consent(device_id, False, "data_deleted")
        
        return {
            "success": True,
            "message": "All analytics data deleted successfully",
            "data": {
                "records_deleted": deleted_count,
                "consent_status": "revoked",
                "deletion_date": datetime.now(timezone.utc).isoformat(),
                "note": "Analytics consent has been revoked and all data removed"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user data")

@router.post("/export")
async def export_user_data(request: DataExportRequest):
    """Export all user data (GDPR data portability)"""
    try:
        device_token = validate_device_token(request.device_token)
        
        # Get device ID
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Export data using privacy service
        export_data = await privacy_analytics_service.export_user_data(device_id)
        
        if not export_data:
            raise HTTPException(status_code=500, detail="Failed to export user data")
        
        return {
            "success": True,
            "message": "User data exported successfully",
            "data": export_data,
            "export_info": {
                "format": "JSON",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "includes": [
                    "Device registration data",
                    "Analytics events (if consented)",
                    "Privacy preferences",
                    "Consent history"
                ],
                "note": "This export contains all data associated with your device"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")

@router.get("/policy")
async def get_privacy_policy():
    """Get current privacy policy and data practices"""
    return {
        "success": True,
        "data": {
            "privacy_policy": {
                "version": "1.0",
                "effective_date": "2025-07-13",
                "last_updated": "2025-07-13"
            },
            "data_collection": {
                "what_we_collect": [
                    "Device registration information",
                    "Job search keywords and preferences",
                    "App usage analytics (with consent)",
                    "Notification interaction data (with consent)"
                ],
                "why_we_collect": [
                    "To provide job notification services",
                    "To improve app functionality (with consent)",
                    "To generate anonymous usage statistics"
                ],
                "data_retention": "Analytics data is kept while consent is active. Registration data is kept until account deletion."
            },
            "your_rights": {
                "consent": "Grant or revoke analytics consent at any time",
                "access": "Request a copy of your personal data",
                "deletion": "Request deletion of your personal data",
                "portability": "Export your data in machine-readable format",
                "objection": "Object to processing of your data"
            },
            "contact": {
                "data_protection": "privacy@yourapp.com",
                "support": "support@yourapp.com"
            },
            "legal_basis": {
                "service_provision": "Contract performance (job notifications)",
                "analytics": "Explicit consent",
                "legitimate_interest": "Anonymous app improvement"
            }
        }
    }

@router.get("/analytics/anonymous")
async def get_anonymous_analytics():
    """Get anonymous analytics summary (no user consent required)"""
    try:
        # Get anonymous analytics that don't identify users
        summary = await privacy_analytics_service.get_analytics_summary_anonymous()
        
        return {
            "success": True,
            "message": "Anonymous analytics retrieved",
            "data": summary,
            "privacy_note": "This data is fully anonymized and contains no personally identifiable information"
        }
        
    except Exception as e:
        logger.error(f"Error getting anonymous analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")