from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365  # 1 year for device tokens

security = HTTPBearer(auto_error=False)

class APIKeyAuth:
    """Simple API key authentication for admin endpoints"""
    
    def __init__(self, valid_api_keys: set):
        self.valid_api_keys = valid_api_keys
    
    def __call__(self, request: Request) -> bool:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in self.valid_api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        return True

class DeviceAuth:
    """Device-based authentication using signed tokens"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_device_token(self, device_id: str) -> str:
        """Generate JWT token for device"""
        payload = {
            'device_id': device_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)
    
    def verify_device_token(self, token: str) -> str:
        """Verify device token and return device_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            device_id = payload.get('device_id')
            if device_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            return device_id
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid device token"
            )

# Global instances
api_key_auth = APIKeyAuth({settings.API_KEY})
device_auth = DeviceAuth(settings.SECRET_KEY)

def get_current_device(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get current device from JWT token (optional)"""
    if not credentials:
        return None
    
    try:
        return device_auth.verify_device_token(credentials.credentials)
    except HTTPException:
        return None

def require_device_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Require valid device authentication"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return device_auth.verify_device_token(credentials.credentials)

def require_api_key(request: Request) -> bool:
    """Require valid API key for admin endpoints"""
    return api_key_auth(request)

def setup_security_headers(app):
    """Setup security headers middleware"""
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS for HTTPS
        if request.url.scheme == "https":
            response.headers['Strict-Transport-Security'] = \
                'max-age=31536000; includeSubDomains'
        
        # CSP for API responses
        response.headers['Content-Security-Policy'] = "default-src 'none'"
        
        return response

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)