#!/usr/bin/env python3
"""
Deployment script for Render.com
"""
import subprocess
import sys
import json
import os
from pathlib import Path

def run_command(command, description, check=True):
    """Run a command and handle errors"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if check:
            print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stderr)
        return False

def check_environment():
    """Check if required tools are available"""
    print("🔍 Checking deployment environment...")
    
    # Check Git
    if not run_command("git --version", "Checking Git installation", check=False):
        print("❌ Git is required for deployment")
        return False
    
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("❌ This is not a Git repository. Please initialize git first:")
        print("   git init")
        print("   git add .")
        print("   git commit -m 'Initial commit'")
        return False
    
    # Check if render.yaml exists
    if not Path("render.yaml").exists():
        print("❌ render.yaml not found")
        return False
    
    print("✅ Environment check passed")
    return True

def prepare_deployment():
    """Prepare the project for deployment"""
    print("📦 Preparing deployment...")
    
    # Check if there are uncommitted changes
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️  You have uncommitted changes:")
        print(result.stdout)
        
        commit = input("Would you like to commit these changes? (y/n): ").lower().strip()
        if commit == 'y':
            message = input("Enter commit message: ").strip()
            if not message:
                message = "Deploy updates"
            
            if not run_command("git add .", "Adding files to git"):
                return False
            
            if not run_command(f'git commit -m "{message}"', "Committing changes"):
                return False
        else:
            print("❌ Please commit your changes before deploying")
            return False
    
    # Check if we have a remote repository
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("❌ No git remote found. Please add a remote repository:")
        print("   git remote add origin <your-repo-url>")
        return False
    
    print("✅ Project is ready for deployment")
    return True

def deploy_to_render():
    """Deploy to Render.com"""
    print("🚀 Deploying to Render...")
    
    print("📋 Deployment Steps:")
    print("1. Push your code to GitHub/GitLab")
    print("2. Connect your repository to Render")
    print("3. Create services using render.yaml")
    
    # Push to remote
    push = input("Push to remote repository? (y/n): ").lower().strip()
    if push == 'y':
        if not run_command("git push", "Pushing to remote repository"):
            print("❌ Failed to push to remote. Please check your git configuration.")
            return False
    
    print("\n📖 Next steps:")
    print("1. Go to https://render.com and sign up/log in")
    print("2. Click 'New' → 'Blueprint'")
    print("3. Connect your GitHub/GitLab repository")
    print("4. Render will automatically detect render.yaml and create services")
    
    print("\n🔧 Required Environment Variables:")
    print("- DATABASE_URL: Auto-configured from PostgreSQL service")
    print("- REDIS_URL: Auto-configured from Redis service")
    print("- SECRET_KEY: Auto-generated")
    print("- API_KEY: Auto-generated")
    print("- APNS_KEY_PATH: Upload your APNs .p8 file")
    print("- APNS_KEY_ID: Your APNs Key ID")
    print("- APNS_TEAM_ID: Your Apple Team ID")
    print("- APNS_BUNDLE_ID: Your iOS app bundle ID")
    
    print("\n📱 APNs Setup:")
    print("1. Upload your .p8 file to Render's file storage")
    print("2. Set APNS_KEY_PATH to the uploaded file path")
    print("3. Update other APNS_* environment variables")
    
    return True

def show_post_deployment():
    """Show post-deployment instructions"""
    print("\n🎉 Deployment Configuration Complete!")
    print("=" * 50)
    
    print("\n🔗 Your services will be available at:")
    print("- API: https://birjob-ios-api.onrender.com")
    print("- Health Check: https://birjob-ios-api.onrender.com/api/v1/health")
    print("- API Docs: https://birjob-ios-api.onrender.com/docs")
    
    print("\n⚙️  Monitor your deployment:")
    print("1. Check service logs in Render dashboard")
    print("2. Verify health check endpoints")
    print("3. Test API endpoints")
    print("4. Monitor background job processing")
    
    print("\n🔍 Troubleshooting:")
    print("- Check logs if services fail to start")
    print("- Verify environment variables are set correctly")
    print("- Ensure database migrations ran successfully")
    print("- Test Redis connectivity")

def main():
    """Main deployment function"""
    print("🚀 iOS Backend Deployment to Render.com")
    print("=" * 50)
    
    if not check_environment():
        return False
    
    if not prepare_deployment():
        return False
    
    if not deploy_to_render():
        return False
    
    show_post_deployment()
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)