#!/usr/bin/env python3
"""
Test the push notification endpoint directly
"""
import requests
import json

# Test data
device_token = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'
user_id = '185c4f0a-531c-404a-8e4b-94e4727c9bb7'  # From previous logs

def test_push_endpoint():
    """Test the push notification endpoint"""
    print("=== Testing Push Notification Endpoint ===")
    
    # Test notification payload
    payload = {
        "device_token": device_token,
        "message": {
            "title": "New Key Test",
            "body": "Testing push notifications with new APNs key",
            "data": {
                "type": "test",
                "timestamp": "2025-07-07T20:30:00Z"
            }
        }
    }
    
    print(f"Sending to device: {device_token}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make request to local server (if running)
        url = "http://localhost:8000/test/push"  # Adjust URL if needed
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Push notification endpoint responded successfully!")
        else:
            print("❌ FAILED: Push notification endpoint returned error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure your server is running on localhost:8000")
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_push_endpoint()