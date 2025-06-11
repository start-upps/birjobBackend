#!/usr/bin/env python3
"""
Demo script to show iOS Backend API endpoints
This demonstrates the API structure without requiring full database setup
"""

from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
import json
from datetime import datetime
import uuid

# Mock data for demonstration
mock_devices = {}
mock_subscriptions = {}
mock_matches = {}

app = FastAPI(
    title="iOS Native App Backend - DEMO",
    description="Demo version showing API endpoints",
    version="1.0.0"
)

# Device Management Endpoints
@app.post("/api/v1/devices/register")
async def register_device(request: Dict[str, Any]):
    """Register a new iOS device for push notifications"""
    device_id = str(uuid.uuid4())
    mock_devices[device_id] = {
        "device_token": request.get("device_token"),
        "device_info": request.get("device_info"),
        "registered_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    return {
        "success": True,
        "data": {
            "device_id": device_id,
            "registered_at": mock_devices[device_id]["registered_at"]
        }
    }

@app.delete("/api/v1/devices/{device_id}")
async def unregister_device(device_id: str):
    """Unregister a device from push notifications"""
    if device_id not in mock_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    mock_devices[device_id]["is_active"] = False
    return {"success": True, "message": "Device unregistered successfully"}

@app.get("/api/v1/devices/{device_id}/status")
async def get_device_status(device_id: str):
    """Get device registration status"""
    if device_id not in mock_devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "success": True,
        "data": mock_devices[device_id]
    }

# Keyword Management Endpoints
@app.post("/api/v1/keywords")
async def create_keyword_subscription(request: Dict[str, Any]):
    """Subscribe a device to keyword-based job notifications"""
    subscription_id = str(uuid.uuid4())
    mock_subscriptions[subscription_id] = {
        "device_id": request.get("device_id"),
        "keywords": request.get("keywords", []),
        "sources": request.get("sources", []),
        "location_filters": request.get("location_filters"),
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "data": {
            "subscription_id": subscription_id,
            "keywords_count": len(request.get("keywords", [])),
            "sources_count": len(request.get("sources", [])),
            "created_at": mock_subscriptions[subscription_id]["created_at"]
        }
    }

@app.get("/api/v1/keywords/{device_id}")
async def get_keyword_subscriptions(device_id: str):
    """Retrieve current keyword subscriptions for a device"""
    device_subscriptions = [
        {**sub, "subscription_id": sub_id} 
        for sub_id, sub in mock_subscriptions.items() 
        if sub["device_id"] == device_id
    ]
    
    return {
        "success": True,
        "data": {"subscriptions": device_subscriptions}
    }

@app.put("/api/v1/keywords/{subscription_id}")
async def update_keyword_subscription(subscription_id: str, request: Dict[str, Any]):
    """Update keyword subscription settings"""
    if subscription_id not in mock_subscriptions:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    mock_subscriptions[subscription_id].update({
        "keywords": request.get("keywords", []),
        "sources": request.get("sources", []),
        "location_filters": request.get("location_filters"),
        "updated_at": datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "data": {
            "subscription_id": subscription_id,
            "updated_at": mock_subscriptions[subscription_id]["updated_at"]
        }
    }

@app.delete("/api/v1/keywords/{subscription_id}")
async def delete_keyword_subscription(subscription_id: str, device_id: str):
    """Remove a keyword subscription"""
    if subscription_id not in mock_subscriptions:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    del mock_subscriptions[subscription_id]
    return {"success": True, "message": "Keyword subscription removed successfully"}

# Job Matching Endpoints
@app.get("/api/v1/matches/{device_id}")
async def get_job_matches(device_id: str, limit: int = 20, offset: int = 0):
    """Retrieve recent job matches for a device"""
    # Mock job matches
    sample_matches = [
        {
            "match_id": str(uuid.uuid4()),
            "job": {
                "id": 12345,
                "title": "Senior Python Developer",
                "company": "TechCorp Inc.",
                "apply_link": "https://example.com/apply/12345",
                "source": "linkedin",
                "posted_at": "2024-01-16T08:00:00Z"
            },
            "matched_keywords": ["Python", "Senior Developer"],
            "relevance_score": 0.85,
            "matched_at": "2024-01-16T08:30:00Z"
        },
        {
            "match_id": str(uuid.uuid4()),
            "job": {
                "id": 12346,
                "title": "Full Stack Engineer",
                "company": "StartupXYZ",
                "apply_link": "https://example.com/apply/12346",
                "source": "indeed",
                "posted_at": "2024-01-16T09:00:00Z"
            },
            "matched_keywords": ["Python", "Full Stack"],
            "relevance_score": 0.78,
            "matched_at": "2024-01-16T09:15:00Z"
        }
    ]
    
    return {
        "success": True,
        "data": {
            "matches": sample_matches[offset:offset+limit],
            "pagination": {
                "total": len(sample_matches),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(sample_matches)
            }
        }
    }

@app.post("/api/v1/matches/{match_id}/read")
async def mark_match_as_read(match_id: str, device_id: str):
    """Mark a job match as read/viewed"""
    return {"success": True, "message": "Match marked as read"}

@app.get("/api/v1/matches/{device_id}/unread-count")
async def get_unread_count(device_id: str):
    """Get count of unread matches for a device"""
    return {
        "success": True,
        "data": {"unread_count": 3}
    }

# Health & Status Endpoints
@app.get("/api/v1/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "apns": "healthy",
            "scraper": "healthy"
        },
        "metrics": {
            "active_devices": len([d for d in mock_devices.values() if d.get("is_active")]),
            "active_subscriptions": len(mock_subscriptions),
            "matches_last_24h": 15,
            "notifications_sent_last_24h": 8
        }
    }

@app.get("/api/v1/health/status/scraper")
async def scraper_status():
    """Detailed scraper status and statistics"""
    return {
        "status": "running",
        "last_run": "2024-01-16T10:15:00Z",
        "next_run": "2024-01-16T10:30:00Z",
        "sources": [
            {
                "name": "linkedin",
                "status": "healthy",
                "last_successful_scrape": "2024-01-16T10:15:00Z",
                "jobs_scraped_last_run": 45,
                "error_count_24h": 0
            },
            {
                "name": "indeed",
                "status": "healthy",
                "last_successful_scrape": "2024-01-16T10:12:00Z",
                "jobs_scraped_last_run": 32,
                "error_count_24h": 1
            }
        ],
        "total_jobs_last_24h": 234,
        "errors_last_24h": 1
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "iOS Native App Backend API - Demo Version",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "devices": "/api/v1/devices/*",
            "keywords": "/api/v1/keywords/*",
            "matches": "/api/v1/matches/*"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting iOS Backend API Demo...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/api/v1/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)