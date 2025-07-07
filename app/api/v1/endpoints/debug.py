from fastapi import APIRouter
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/apns-key-debug")
async def debug_apns_key():
    """Debug APNs key format in production"""
    
    result = {
        "has_env_var": bool(settings.APNS_PRIVATE_KEY),
        "key_id": settings.APNS_KEY_ID,
        "team_id": settings.APNS_TEAM_ID,
        "bundle_id": settings.APNS_BUNDLE_ID,
        "sandbox": settings.APNS_SANDBOX
    }
    
    if settings.APNS_PRIVATE_KEY:
        key = settings.APNS_PRIVATE_KEY
        result.update({
            "key_length": len(key),
            "starts_with_quote": key.startswith('"'),
            "ends_with_quote": key.endswith('"'),
            "has_escaped_newlines": '\\n' in key,
            "starts_with_begin": key.startswith('-----BEGIN PRIVATE KEY-----'),
            "ends_with_end": key.strip().endswith('-----END PRIVATE KEY-----'),
            "first_50_chars": repr(key[:50]),
            "last_50_chars": repr(key[-50:])
        })
        
        # Try cleaning
        cleaned = key.strip()
        while cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()
        
        if '\\n' in cleaned:
            cleaned = cleaned.replace('\\n', '\n')
            
        result.update({
            "cleaned_length": len(cleaned),
            "cleaned_starts_correct": cleaned.startswith('-----BEGIN PRIVATE KEY-----'),
            "cleaned_ends_correct": cleaned.strip().endswith('-----END PRIVATE KEY-----'),
            "cleaned_first_30": repr(cleaned[:30]),
            "cleaned_last_30": repr(cleaned[-30:])
        })
        
        # Test cryptography
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            private_key = load_pem_private_key(cleaned.encode(), password=None)
            result["cryptography_test"] = "SUCCESS"
            result["key_type"] = str(type(private_key))
        except Exception as e:
            result["cryptography_test"] = f"FAILED: {str(e)}"
    
    return result