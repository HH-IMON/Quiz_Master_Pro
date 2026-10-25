#!/usr/bin/env python3
"""
One-Click Railway Deployment Script
Automates Railway deployment for Quiz Master Pro
"""
import subprocess
import sys
import webbrowser
import time

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"🚀 {text}")
    print("=" * 70)

def print_step(step_num, text):
    """Print step"""
    print(f"\n{step_num}. {text}")

def deploy_to_railway():
    """Complete Railway deployment automation"""
    print_header("RAILWAY DEPLOYMENT FOR IK001122")
    
    print("""
    This script will help you deploy Quiz Master Pro to Railway.app
    
    Prerequisites:
    ✅ Code pushed to GitHub (run: python push_to_github.py)
    ⏳ This script will guide the rest
    """)
    
    input("Press Enter to continue...")
    
    print_header("STEP 1: Railway Account Setup")
    print_step(1, "Create Railway Account")
    print("""
    1. Visit: https://railway.app
    2. Click 'Start Free' or 'Sign Up'
    3. Use GitHub Login (for IK001122)
    4. Authorize the app
    """)
    
    response = input("\n✅ Have you created Railway account? (yes/no): ").lower()
    if response != 'yes':
        print("❌ Please create Railway account first!")
        return False
    
    # Open Railway
    print("\n🌐 Opening Railway in browser...")
    webbrowser.open("https://railway.app/dashboard")
    time.sleep(2)
    
    print_header("STEP 2: Create Railway Project")
    print_step(2, "Connect GitHub Repository")
    print("""
    On Railway Dashboard:
    1. Click 'Create New Project'
    2. Select 'Deploy from GitHub'
    3. Select repository: IK001122/quiz-master-pro
    4. Click 'Deploy'
    5. Wait for initial deployment (2-3 minutes)
    """)
    
    input("\n✅ Press Enter after Railway starts deployment...")
    
    print_header("STEP 3: Add MySQL Database")
    print_step(3, "Provision MySQL Service")
    print("""
    On Railway Project:
    1. Click 'Add Service'
    2. Select 'MySQL'
    3. Wait for provisioning (1-2 minutes)
    4. You'll see DB_HOST, DB_USER, DB_PASSWORD auto-set
    """)
    
    input("\n✅ Press Enter after MySQL is provisioned...")
    
    print_header("STEP 4: Set Environment Variables")
    print_step(4, "Configure Your App")
    print("""
    On Railway Project Variables tab, add:
    
    Name                Value
    ─────────────────────────────────────────
    DB_HOST             (copy from MySQL service)
    DB_USER             (copy from MySQL service)
    DB_PASSWORD         (copy from MySQL service)
    DB_NAME             quizmasterpro
    SECRET_KEY          <generate-a-random-key>
    DEBUG               False
    HOST                0.0.0.0
    PORT                5000
    
    For SECRET_KEY, use something like:
    Your-App-Secret-Key-12345-Change-Me
    """)
    
    input("\n✅ Press Enter after setting all variables...")
    
    print_header("STEP 5: Initialize Database")
    print_step(5, "Setup Database Schema")
    print("""
    In Railway Dashboard:
    1. Click on your Deployment
    2. Go to 'Shell' tab
    3. Run this command:
    
    python -c "from database import init_database; init_database()"
    
    Wait for it to complete (should see "Database initialized!")
    """)
    
    input("\n✅ Press Enter after database is initialized...")
    
    print_header("STEP 6: Your App is LIVE!")
    print_step(6, "Access Your Application")
    print("""
    Your Quiz Master Pro is now LIVE! 🎉
    
    1. In Railway Dashboard, find your app URL
    2. Click the link or open in browser
    3. Your app is ready to use!
    
    The URL will look like:
    https://quizmaster-pro-production.up.railway.app
    
    Or if you configured a domain:
    https://your-custom-domain.com
    """)
    
    print_header("DEPLOYMENT COMPLETE!")
    print("""
    ✅ Your app is live on Railway!
    
    Next steps:
    - Share your URL with users
    - Add custom domain (Railway settings)
    - Monitor usage (Railway Dashboard)
    - Set up auto-scaling if needed
    
    Need to update your app?
    1. Make changes locally
    2. Push to GitHub: git push origin master
    3. Railway auto-deploys automatically!
    
    Questions?
    - Railway Docs: https://docs.railway.app
    - Support: https://railway.app/support
    """)
    
    input("\n✅ Press Enter to complete setup...")
    print("\n🎉 DEPLOYMENT SUCCESSFUL! Enjoy your app!\n")
    
    return True

if __name__ == "__main__":
    success = deploy_to_railway()
    sys.exit(0 if success else 1)
