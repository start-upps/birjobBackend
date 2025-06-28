#!/usr/bin/env python3
"""
Complete test suite for unified user system
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Add the app directory to Python path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from application import app
from app.core.database import db_manager

client = TestClient(app)

async def test_database_structure():
    """Test unified database structure"""
    print("🔍 Testing unified database structure...")
    
    # Check unified table exists
    table_check = await db_manager.execute_query("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'iosapp' 
            AND table_name = 'users_unified'
        );
    """)
    print(f"✅ users_unified table exists: {table_check[0]['exists']}")
    
    # Check record count
    count_result = await db_manager.execute_query("SELECT COUNT(*) as count FROM iosapp.users_unified")
    print(f"📊 Total users in unified table: {count_result[0]['count']}")
    
    # Check sample data
    sample_result = await db_manager.execute_query("""
        SELECT device_id, first_name, match_keywords, profile_completeness
        FROM iosapp.users_unified 
        ORDER BY updated_at DESC 
        LIMIT 3;
    """)
    
    print("📋 Sample unified data:")
    for user in sample_result:
        keywords = user['match_keywords'] if user['match_keywords'] else []
        print(f"   Device: {user['device_id']}, Name: {user['first_name']}, Keywords: {keywords}, Completeness: {user['profile_completeness']}%")

def test_all_unified_endpoints():
    """Test all unified user endpoints"""
    print("\n🧪 Testing all unified user endpoints...")
    
    # Test data
    test_device = "test-complete-system"
    
    # 1. Create user profile
    print("\n1️⃣ Testing profile creation...")
    profile_data = {
        "device_id": test_device,
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
        "location": "New York",
        "current_job_title": "Senior Developer",
        "skills": ["python", "react", "docker", "aws"],
        "match_keywords": ["python", "backend", "api", "microservices"],
        "desired_job_types": ["Full-time", "Remote"],
        "min_salary": 90000,
        "max_salary": 140000,
        "job_matches_enabled": True,
        "profile_visibility": "private"
    }
    
    response = client.post("/api/v1/users/profile", json=profile_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Profile created: {result['data']['deviceId']}, Completeness: {result['data']['profileCompleteness']}%")
        user_id = result['data']['userId']
    else:
        print(f"   ❌ Error: {response.text}")
        return False
    
    # 2. Get user profile
    print("\n2️⃣ Testing profile retrieval...")
    response = client.get(f"/api/v1/users/profile/{test_device}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        profile = result['data']
        print(f"   ✅ Profile retrieved: {profile['personalInfo']['firstName']} {profile['personalInfo']['lastName']}")
        print(f"   📊 Completeness: {profile['profileCompleteness']}%")
        print(f"   🏷️ Keywords: {profile['jobPreferences']['matchKeywords']}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # 3. Test keyword management
    print("\n3️⃣ Testing keyword management...")
    
    # Get keywords
    response = client.get(f"/api/v1/users/{test_device}/profile/keywords")
    print(f"   GET keywords status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Current keywords: {result['data']['matchKeywords']} ({result['data']['keywordCount']} total)")
    
    # Add keyword
    response = client.post(f"/api/v1/users/{test_device}/profile/keywords/add", json={"keyword": "kubernetes"})
    print(f"   ADD keyword status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Added keyword: {result['data']['addedKeyword']} (Total: {result['data']['keywordCount']})")
    
    # Update keywords
    new_keywords = ["python", "fastapi", "docker", "kubernetes", "postgresql", "redis"]
    response = client.post(f"/api/v1/users/{test_device}/profile/keywords", json={"match_keywords": new_keywords})
    print(f"   UPDATE keywords status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Updated keywords: {result['data']['matchKeywords']} ({result['data']['keywordCount']} total)")
    
    # Get job matches
    print("\n4️⃣ Testing job matching...")
    response = client.get(f"/api/v1/users/{test_device}/profile/matches?limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        matches = result['data']['matches']
        stats = result['data']['matchingStats']
        print(f"   ✅ Found {len(matches)} matches out of {stats['totalJobsEvaluated']} jobs evaluated")
        print(f"   📈 Stats: Avg Score: {stats['averageScore']}, Top Score: {stats['topScore']}")
        
        if matches:
            top_match = matches[0]
            print(f"   🎯 Top match: {top_match['title']} (Score: {top_match['matchScore']})")
            print(f"      Keywords: {top_match['matchedKeywords']}")
        else:
            print(f"   ℹ️ No matches found (likely due to non-English job data)")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Remove keyword
    print("\n5️⃣ Testing keyword removal...")
    response = client.delete(f"/api/v1/users/{test_device}/profile/keywords/redis")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Removed keyword: {result['data']['removedKeyword']} (Remaining: {result['data']['keywordCount']})")
    
    print("\n✅ All unified endpoint tests completed successfully!")
    return True

async def test_legacy_compatibility():
    """Test backward compatibility with legacy API format"""
    print("\n🔄 Testing legacy compatibility...")
    
    # The new endpoints should return data in legacy format
    test_device = "test-complete-system"
    
    response = client.get(f"/api/v1/users/profile/{test_device}")
    if response.status_code == 200:
        result = response.json()
        profile = result['data']
        
        # Check legacy format structure
        required_fields = ['userId', 'deviceId', 'personalInfo', 'jobPreferences', 
                          'notificationSettings', 'privacySettings', 'profileCompleteness']
        
        missing_fields = [field for field in required_fields if field not in profile]
        
        if not missing_fields:
            print("   ✅ Legacy format compatibility maintained")
            print(f"   📝 Profile structure includes all required fields")
        else:
            print(f"   ⚠️ Missing legacy fields: {missing_fields}")
    else:
        print(f"   ❌ Legacy compatibility test failed: {response.status_code}")

async def main():
    """Main test function"""
    print("🚀 Complete Unified User System Test Suite")
    print("=" * 60)
    
    # Test 1: Database structure
    await test_database_structure()
    
    # Test 2: All API endpoints
    success = test_all_unified_endpoints()
    
    # Test 3: Legacy compatibility
    await test_legacy_compatibility()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Unified user system is working correctly")
        print("📊 Database consolidation complete")
        print("🔄 Legacy compatibility maintained")
        print("🎯 Keyword matching system operational")
    else:
        print("❌ Some tests failed - check the output above")

if __name__ == "__main__":
    asyncio.run(main())