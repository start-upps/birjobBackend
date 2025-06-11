#!/usr/bin/env python3
"""
Database migration script for iOS Backend
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stderr)
        return False

def main():
    """Main migration function"""
    print("📊 iOS Backend Database Migration")
    print("=" * 40)
    
    # Check if alembic is available
    if not run_command("python -c 'import alembic'", "Checking Alembic installation"):
        print("Please install Alembic: pip install alembic")
        return False
    
    # Check if we're in the right directory
    if not Path("alembic.ini").exists():
        print("❌ alembic.ini not found. Please run this script from the project root.")
        return False
    
    # Show current migration status
    print("\n📋 Current migration status:")
    run_command("alembic current", "Getting current migration")
    
    # Show pending migrations
    print("\n📋 Pending migrations:")
    run_command("alembic heads", "Getting migration heads")
    
    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Run migrations (upgrade to latest)")
    print("2. Create new migration")
    print("3. Show migration history")
    print("4. Reset database (downgrade all)")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        # Run migrations
        if run_command("alembic upgrade head", "Running migrations to latest"):
            print("\n🎉 Database is now up to date!")
            run_command("alembic current", "Current migration status")
    
    elif choice == "2":
        # Create new migration
        message = input("Enter migration message: ").strip()
        if message:
            command = f'alembic revision --autogenerate -m "{message}"'
            run_command(command, f"Creating migration: {message}")
        else:
            print("❌ Migration message is required")
    
    elif choice == "3":
        # Show history
        run_command("alembic history", "Migration history")
    
    elif choice == "4":
        # Reset database
        confirm = input("⚠️  This will reset the entire database. Type 'YES' to confirm: ")
        if confirm == "YES":
            run_command("alembic downgrade base", "Resetting database")
            print("🔄 Database reset complete. Run option 1 to apply migrations again.")
        else:
            print("❌ Reset cancelled")
    
    elif choice == "5":
        print("👋 Goodbye!")
        return True
    
    else:
        print("❌ Invalid choice")
        return False
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)