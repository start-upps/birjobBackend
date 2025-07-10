"""
Validation utilities for data integrity
"""
from fastapi import HTTPException
import re

def validate_device_token(device_token: str) -> str:
    """
    Validate APNs device token format and prevent bad data entry
    
    Args:
        device_token: Raw device token string
        
    Returns:
        str: Validated and cleaned device token
        
    Raises:
        HTTPException: If token is invalid
    """
    if not device_token:
        raise HTTPException(status_code=400, detail="device_token is required")
    
    if not isinstance(device_token, str):
        raise HTTPException(status_code=400, detail="device_token must be a string")
    
    # Clean whitespace
    device_token = device_token.strip()
    
    # Validate APNs token format (64 hex characters)
    if len(device_token) != 64:
        raise HTTPException(
            status_code=400, 
            detail=f"device_token must be exactly 64 characters (got {len(device_token)})"
        )
    
    # Check if it's hex only
    try:
        int(device_token, 16)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="device_token must contain only hexadecimal characters (0-9, a-f)"
        )
    
    # Prevent temporary/fake tokens that bypass real validation
    forbidden_prefixes = ('temp_', 'placeholder_', 'fake_', 'test_', 'mock_', 'dummy_')
    if device_token.lower().startswith(forbidden_prefixes):
        raise HTTPException(
            status_code=400, 
            detail="Invalid device_token: temporary or placeholder tokens not allowed"
        )
    
    # Additional check for obviously fake tokens
    if device_token == '0' * 64 or device_token == 'f' * 64:
        raise HTTPException(
            status_code=400, 
            detail="Invalid device_token: obviously fake tokens not allowed"
        )
    
    return device_token

def validate_device_id(device_id: str) -> str:
    """
    Validate device ID format
    
    Args:
        device_id: Raw device ID string
        
    Returns:
        str: Validated and cleaned device ID
        
    Raises:
        HTTPException: If device ID is invalid
    """
    if not device_id or not isinstance(device_id, str):
        raise HTTPException(status_code=400, detail="device_id is required and must be a string")
    
    device_id = device_id.strip()
    
    if len(device_id) < 8:
        raise HTTPException(status_code=400, detail="device_id must be at least 8 characters")
    
    if len(device_id) > 255:
        raise HTTPException(status_code=400, detail="device_id must be less than 255 characters")
    
    return device_id

def validate_email(email: str) -> str:
    """
    Validate email format
    
    Args:
        email: Raw email string
        
    Returns:
        str: Validated and cleaned email
        
    Raises:
        HTTPException: If email is invalid
    """
    if not email:
        return email  # Allow empty email in some cases
    
    if not isinstance(email, str):
        raise HTTPException(status_code=400, detail="email must be a string")
    
    email = email.strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    return email

def validate_keywords(keywords: list) -> list:
    """
    Validate keywords array
    
    Args:
        keywords: Raw keywords list
        
    Returns:
        list: Validated and cleaned keywords
        
    Raises:
        HTTPException: If keywords are invalid
    """
    if keywords is None:
        return []
    
    if not isinstance(keywords, list):
        raise HTTPException(status_code=400, detail="keywords must be an array")
    
    # Limit keywords count
    if len(keywords) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 keywords allowed")
    
    validated_keywords = []
    for keyword in keywords:
        if not isinstance(keyword, str):
            raise HTTPException(status_code=400, detail="Each keyword must be a string")
        
        keyword = keyword.strip()
        
        if len(keyword) == 0:
            continue  # Skip empty keywords
        
        if len(keyword) > 100:
            raise HTTPException(status_code=400, detail="Each keyword must be less than 100 characters")
        
        # Prevent duplicate keywords (case-insensitive)
        if keyword.lower() not in [k.lower() for k in validated_keywords]:
            validated_keywords.append(keyword)
    
    return validated_keywords