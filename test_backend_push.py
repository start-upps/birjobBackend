#!/usr/bin/env python3
"""
Test backend push notification service with new key
"""
import asyncio
import sys
import os

# Add the project directory to path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.services.push_notifications import PushNotificationService

async def test_backend_push_service():
    """Test the backend push notification service"""
    print("=== Testing Backend Push Notification Service ===")
    
    # Initialize the service
    push_service = PushNotificationService()
    
    # Test device token from iOS app
    device_token = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'
    device_id = 'test-device'
    
    # Test job match notification
    job = {
        'id': 'test-job-123',
        'title': 'Software Engineer',
        'company': 'Test Company',
        'source': 'test'
    }
    
    matched_keywords = ['python', 'backend']
    match_id = 'test-match-123'
    
    print(f"Sending job match notification to device: {device_token}")
    print(f"Job: {job['title']} at {job['company']}")
    print(f"Matched keywords: {matched_keywords}")
    
    try:
        # Send the notification
        success = await push_service.send_job_match_notification(
            device_token=device_token,
            device_id=device_id,
            job=job,
            matched_keywords=matched_keywords,
            match_id=match_id
        )
        
        if success:
            print("✅ SUCCESS: Push notification sent successfully!")
        else:
            print("❌ FAILED: Push notification failed to send")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_backend_push_service())