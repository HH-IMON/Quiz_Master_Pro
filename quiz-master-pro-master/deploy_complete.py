#!/usr/bin/env python3
"""
🚀 QUIZ MASTER PRO - COMPLETE DEPLOYMENT AUTOMATION
One script to deploy EVERYTHING for user: IK001122
"""
import subprocess
import sys
import os
import time

def print_banner():
    """Print deployment banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║       🚀 QUIZ MASTER PRO - DEPLOYMENT AUTOMATION 🚀       ║
    ║                                                            ║
    ║              for GitHub User: IK001122                    ║
    ║                                                            ║
    ║              ONE SCRIPT TO DEPLOY EVERYTHING!             ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("\n📋 Checking prerequisites...")
    
    # Check git
    result = subprocess.run(['git', '--version'], capture_output=True)
    if result.returncode != 0:
        print("❌ Git not installed!")
        return False
    print("✅ Git installed")
    
    # Check Python
    print(f"✅ Python {sys.version.split()[0]} installed")
    
    # Check if repo is initialized
    if not os.path.exists('.git'):
        print("⚠️  Git repository not initialized. Initializing...")
        subprocess.run(['git', 'init'], capture_output=True)
        print("✅ Git repository initialized")
    
    return True

def show_menu():
    """Show deployment menu"""
    print("\n" + "=" * 60)
    print("📌 DEPLOYMENT MENU")
    print("=" * 60)
    print("""
    What would you like to do?
    
    1. 🔗 PUSH CODE TO GITHUB
       Push your code to: github.com/IK001122/quiz-master-pro
    
    2. 🚀 DEPLOY TO RAILWAY
       Deploy to Railway.app (FREE with $5/month credit)
    
    3. 📚 VIEW DOCUMENTATION
       Read deployment guides and troubleshooting
    
    4. 🎯 COMPLETE GUIDED SETUP
       Step-by-step setup wizard for everything
    
    5. ❌ EXIT
    """)
    
    choice = input("Select option (1-5): ").strip()
    return choice

def deploy_github():
    """Push to GitHub"""
    print("\n" + "=" * 60)
    print("🔗 GITHUB DEPLOYMENT")
    print("=" * 60)
    
    github_username = "IK001122"
    repo_name = "quiz-master-pro"
    
    print(f"""
    This will push your code to:
    github.com/{github_username}/{repo_name}
    
    BEFORE CONTINUING:
    1. Create empty repo at: https://github.com/new
       Name it: {repo_name}
    
    2. Generate GitHub Token: https://github.com/settings/tokens
       Click 'Generate new token'
       Select 'repo' scope
       Copy the token
    
    3. Use your GitHub token as password when prompted
    """)
    
    if input("\nReady to push? (yes/no): ").lower() == 'yes':
        # Run push script
        result = subprocess.run([sys.executable, 'push_to_github.py'])
        return result.returncode == 0
    
    return False

def deploy_railway():
    """Deploy to Railway"""
    print("\n" + "=" * 60)
    print("🚀 RAILWAY DEPLOYMENT")
    print("=" * 60)
    
    print("""
    This will guide you through Railway deployment!
    
    Requirements:
    ✅ Code must be pushed to GitHub first
    ⏳ Railway account (free, uses GitHub login)
    """)
    
    if input("\nContinue to Railway deployment? (yes/no): ").lower() == 'yes':
        # Run railway script
        result = subprocess.run([sys.executable, 'deploy_railway.py'])
        return result.returncode == 0
    
    return False

def show_docs():
    """Show documentation"""
    docs = """
    
    📚 QUIZ MASTER PRO - DEPLOYMENT DOCUMENTATION
    
    ════════════════════════════════════════════════════════════
    1. PROJECT STRUCTURE
    ════════════════════════════════════════════════════════════
    
    Your app includes:
    - Flask web framework with WebSocket support
    - MySQL database backend
    - Real-time chat and gaming features
    - Admin dashboard
    - User authentication system
    - Quiz management system
    
    Files created for deployment:
    - Dockerfile          : Container setup
    - railway.json        : Railway configuration
    - .env.example        : Environment variables template
    - requirements.txt    : Python dependencies
    - Procfile            : Process configuration
    
    ════════════════════════════════════════════════════════════
    2. DEPLOYMENT OPTIONS
    ════════════════════════════════════════════════════════════
    
    RECOMMENDED: Railway.app
    - Free tier with $5/month credit
    - Auto-deploys from GitHub
    - MySQL database included
    - Perfect for this project
    
    ALTERNATIVES:
    - Heroku (paid plans only now)
    - Render.com (free tier available)
    - AWS/Google Cloud (more complex)
    
    ════════════════════════════════════════════════════════════
    3. ENVIRONMENT VARIABLES
    ════════════════════════════════════════════════════════════
    
    On your hosting platform, set:
    
    DB_HOST         : Your MySQL host
    DB_USER         : Your MySQL user
    DB_PASSWORD     : Your MySQL password
    DB_NAME         : quizmasterpro
    SECRET_KEY      : Random secure key (change this!)
    DEBUG           : False (for production)
    HOST            : 0.0.0.0
    PORT            : 5000
    
    ════════════════════════════════════════════════════════════
    4. DEPLOYMENT PROCESS
    ════════════════════════════════════════════════════════════
    
    STEP 1: Push to GitHub
    $ python push_to_github.py
    
    STEP 2: Deploy to Railway
    $ python deploy_railway.py
    
    STEP 3: Initialize Database
    In Railway Shell:
    $ python -c "from database import init_database; init_database()"
    
    STEP 4: Your app is LIVE! 🎉
    
    ════════════════════════════════════════════════════════════
    5. MONITORING & MAINTENANCE
    ════════════════════════════════════════════════════════════
    
    View Logs:
    - Railway Dashboard > Deployments > Logs
    
    Update Your App:
    1. Make changes locally
    2. git push origin master
    3. Railway auto-deploys (2-3 minutes)
    
    Scale Your App:
    - Adjust CPU/RAM in Railway settings
    - Add more database connections if needed
    
    Custom Domain:
    - Add domain in Railway project settings
    - Point DNS to Railway
    
    ════════════════════════════════════════════════════════════
    6. TROUBLESHOOTING
    ════════════════════════════════════════════════════════════
    
    App won't start?
    → Check logs in Railway Dashboard
    → Verify environment variables are set
    → Ensure database is initialized
    
    Database connection error?
    → Check DB_HOST, DB_USER, DB_PASSWORD
    → Verify MySQL service is running on Railway
    → Check IP whitelist (Railway usually auto-allows)
    
    WebSocket not connecting?
    → Check browser console for errors
    → Ensure async_mode='threading' is set (already done)
    → Verify server is running (check logs)
    
    Need help?
    → Railway Docs: https://docs.railway.app
    → GitHub Issues: Create issue in your repo
    → Email: support@railway.app
    
    ════════════════════════════════════════════════════════════
    """
    print(docs)
    input("Press Enter to continue...")

def complete_wizard():
    """Complete guided setup wizard"""
    print("\n" + "=" * 60)
    print("🎯 COMPLETE GUIDED SETUP WIZARD")
    print("=" * 60)
    
    print("\nThis wizard will walk you through everything!")
    print("\nLet's get your Quiz Master Pro LIVE on Railway!")
    
    # Step 1: GitHub
    print("\n" + "=" * 60)
    print("STEP 1 of 3: PUSH TO GITHUB")
    print("=" * 60)
    if input("\nStart pushing to GitHub? (yes/no): ").lower() == 'yes':
        if not deploy_github():
            print("❌ GitHub push failed. Please try again.")
            return
    else:
        print("⏭️  Skipping GitHub push")
    
    print("\n✅ GitHub step complete!")
    
    # Step 2: Railway
    print("\n" + "=" * 60)
    print("STEP 2 of 3: DEPLOY TO RAILWAY")
    print("=" * 60)
    if input("\nStart Railway deployment? (yes/no): ").lower() == 'yes':
        if not deploy_railway():
            print("❌ Railway deployment failed. Please try again.")
            return
    else:
        print("⏭️  Skipping Railway deployment")
    
    # Step 3: Summary
    print("\n" + "=" * 60)
    print("STEP 3 of 3: DEPLOYMENT COMPLETE! 🎉")
    print("=" * 60)
    print("""
    Your Quiz Master Pro is now LIVE!
    
    🎯 Your App URL: https://your-project-name.railway.app
    
    📊 Next Steps:
    ✅ Share URL with users
    ✅ Add custom domain (optional)
    ✅ Monitor in Railway Dashboard
    ✅ Update app: git push → auto-deploys
    
    💡 Remember:
    - Free $5/month credit on Railway
    - Auto-deploys on every git push
    - Database is persistent
    - Automatic SSL/HTTPS
    
    📚 Documentation saved in:
    - DEPLOYMENT_CHECKLIST.md
    - DEPLOYMENT_GUIDE.md
    """)

def main():
    """Main menu loop"""
    print_banner()
    
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed!")
        return False
    
    print("\n✅ All prerequisites met!")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            deploy_github()
        elif choice == '2':
            deploy_railway()
        elif choice == '3':
            show_docs()
        elif choice == '4':
            complete_wizard()
        elif choice == '5':
            print("\n👋 Goodbye! Your app is deployment-ready!")
            break
        else:
            print("❌ Invalid option!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Deployment interrupted!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
