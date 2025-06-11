#!/usr/bin/env python3
"""
Simple migration runner for your existing database
"""
import os
import sys
import subprocess

def main():
    print("🗄️ iOS Backend Database Migration")
    print("=" * 40)
    
    # Set up environment
    os.environ['DATABASE_URL'] = 'postgresql+asyncpg://neondb_owner:gocazMi82pXl@ep-white-cloud-a2453ie4.eu-central-1.aws.neon.tech/neondb?sslmode=require'
    
    print("✅ Database URL configured")
    print("📊 Your Neon database will get the iosapp schema")
    print()
    
    # Check if alembic is available
    print("🔍 Checking Alembic...")
    try:
        result = subprocess.run(['python3', '-c', 'import alembic'], capture_output=True)
        if result.returncode != 0:
            print("❌ Alembic not found. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'alembic', 'psycopg2-binary'], check=True)
        print("✅ Alembic ready")
    except Exception as e:
        print(f"❌ Could not set up Alembic: {e}")
        return False
    
    print()
    print("🚀 Running migration...")
    print("This will create the iosapp schema in your Neon database")
    print()
    
    # Run the migration
    try:
        # Show current status
        print("📋 Current migration status:")
        subprocess.run(['python3', '-m', 'alembic', 'current'], check=False)
        
        print()
        print("📈 Running migration to create iosapp schema...")
        result = subprocess.run(['python3', '-m', 'alembic', 'upgrade', 'head'], 
                               capture_output=True, text=True, check=True)
        
        print("✅ Migration completed successfully!")
        print()
        
        # Show final status
        print("📋 Final migration status:")
        subprocess.run(['python3', '-m', 'alembic', 'current'], check=False)
        
        print()
        print("🎉 Your database now has the iosapp schema with these tables:")
        print("  - iosapp.device_tokens")
        print("  - iosapp.keyword_subscriptions") 
        print("  - iosapp.job_matches")
        print("  - iosapp.push_notifications")
        print("  - iosapp.processed_jobs")
        print()
        print("🚀 Ready for deployment to Render!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

if __name__ == "__main__":
    if main():
        print("\n✅ Success! Your backend is ready for Render deployment.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)