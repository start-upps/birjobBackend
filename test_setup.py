#!/usr/bin/env python3
"""
Test script to verify iOS Backend setup
"""
import sys
import importlib
import subprocess
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing Python imports...")
    
    required_modules = [
        'fastapi',
        'uvicorn', 
        'asyncpg',
        'redis',
        'pydantic',
        'pydantic_settings',
        'python_multipart',
        'jose',
        'passlib',
        'structlog',
        'prometheus_client',
        'httpx',
        'cryptography',
        'sqlalchemy',
        'alembic'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All imports successful")
    return True

def test_app_structure():
    """Test that the app structure is correct"""
    print("\n📁 Testing application structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'alembic.ini',
        'render.yaml',
        'DEPLOYMENT.md',
        'app/__init__.py',
        'app/core/config.py',
        'app/core/database.py',
        'app/api/v1/router.py',
        'app/models/device.py',
        'app/services/match_engine.py',
        'alembic/env.py',
        'alembic/versions/0001_initial_iosapp_schema.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def test_alembic_setup():
    """Test Alembic configuration"""
    print("\n🗃️  Testing Alembic setup...")
    
    try:
        result = subprocess.run(['python', '-c', 'import alembic; print("Alembic available")'], 
                               capture_output=True, text=True, check=True)
        print("✅ Alembic is available")
        
        # Test alembic configuration
        if Path('alembic.ini').exists():
            print("✅ alembic.ini found")
        else:
            print("❌ alembic.ini missing")
            return False
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Alembic test failed: {e}")
        return False

def test_app_startup():
    """Test that the app can be imported without errors"""
    print("\n🚀 Testing app startup...")
    
    try:
        # Try to import the main app
        import app
        print("✅ App imports successfully")
        
        # Test configuration
        from app.core.config import settings
        print(f"✅ Configuration loaded (SECRET_KEY: {'***' if settings.SECRET_KEY else 'NOT SET'})")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 iOS Backend Setup Verification")
    print("=" * 40)
    
    tests = [
        ("Python Imports", test_imports),
        ("App Structure", test_app_structure), 
        ("Alembic Setup", test_alembic_setup),
        ("App Startup", test_app_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your backend is ready for deployment.")
        print("\n🚀 Next steps:")
        print("1. Set up environment variables")
        print("2. Run migrations: python migrate.py")
        print("3. Deploy to Render: python deploy.py")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)