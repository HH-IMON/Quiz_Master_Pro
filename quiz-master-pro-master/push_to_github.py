#!/usr/bin/env python3
"""
One-Click GitHub Push Script for IK001122
Automates pushing Quiz Master Pro to GitHub
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n📍 {description}")
    print(f"   Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ❌ Error: {result.stderr}")
            return False
        print(f"   ✅ Success!")
        if result.stdout:
            print(f"   {result.stdout}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def push_to_github():
    """Push code to GitHub"""
    print("=" * 70)
    print("🚀 GITHUB PUSH AUTOMATION FOR: IK001122")
    print("=" * 70)
    
    # Check if git is initialized
    if not os.path.exists('.git'):
        print("❌ Git repository not found! Run 'git init' first.")
        return False
    
    github_username = "IK001122"
    repo_name = "quiz-master-pro"
    repo_url = f"https://github.com/{github_username}/{repo_name}.git"
    
    print(f"\n📋 GitHub Details:")
    print(f"   Username: {github_username}")
    print(f"   Repository: {repo_name}")
    print(f"   URL: {repo_url}")
    
    print(f"\n⚠️  IMPORTANT:")
    print(f"   1. Create an EMPTY repository on GitHub:")
    print(f"      Visit: https://github.com/new")
    print(f"      Name: {repo_name}")
    print(f"      Leave other options default")
    print(f"   2. Create a GitHub Personal Access Token:")
    print(f"      Visit: https://github.com/settings/tokens")
    print(f"      Click 'Generate new token'")
    print(f"      Select 'repo' scope")
    print(f"      Copy the token")
    print(f"   3. When prompted, use token as password")
    
    input("\n✅ Press Enter when ready to push to GitHub...")
    
    # Configure git if needed
    run_command('git config user.email "deploy@quizmaster.local"', "Configuring git email")
    run_command('git config user.name "Quiz Master Deployer"', "Configuring git name")
    
    # Remove existing remote if it exists
    run_command('git remote remove origin', "Removing existing remote (if any)")
    
    # Add new remote
    if not run_command(f'git remote add origin {repo_url}', f"Adding GitHub remote: {repo_url}"):
        return False
    
    # Push to GitHub
    if not run_command('git branch -M master', "Renaming branch to master"):
        return False
    
    if not run_command('git push -u origin master', "Pushing to GitHub"):
        return False
    
    print("\n" + "=" * 70)
    print("✅ CODE PUSHED TO GITHUB SUCCESSFULLY!")
    print("=" * 70)
    print(f"\nYour repository is now available at:")
    print(f"   🔗 https://github.com/{github_username}/{repo_name}")
    print(f"\nNext step: Deploy to Railway!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = push_to_github()
    sys.exit(0 if success else 1)
