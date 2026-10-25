"""
Quiz Master Pro - Configuration
Database and application settings for XAMPP MySQL
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production-quizmasterpro-2024')
    
    # MySQL Database Settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'quizmasterpro')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # SSL Settings (Required for some cloud providers like Railway/Azure)
    DB_SSL = {}
    if os.getenv('DB_SSL_CA'):
        DB_SSL['ssl_ca'] = os.getenv('DB_SSL_CA')
    if os.getenv('DB_SSL_VERIFY_CERT') == 'false':
        DB_SSL['ssl_verify_cert'] = False
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # Default to False for production
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Game Settings
    DEFAULT_TIME_PER_QUESTION = 30  # seconds
    MAX_ROOM_PARTICIPANTS = 50
    XP_PER_CORRECT_ANSWER = 10
    XP_PER_STREAK_BONUS = 5
    XP_PER_SPEED_BONUS = 3
    
    # Level System
    LEVELS = {
        1: {'name': 'Beginner', 'xp_required': 0, 'badge': '🌱'},
        2: {'name': 'Learner', 'xp_required': 100, 'badge': '📚'},
        3: {'name': 'Scholar', 'xp_required': 300, 'badge': '🎓'},
        4: {'name': 'Expert', 'xp_required': 600, 'badge': '⭐'},
        5: {'name': 'Master', 'xp_required': 1000, 'badge': '👑'},
        6: {'name': 'Grandmaster', 'xp_required': 1500, 'badge': '🏆'},
        7: {'name': 'Legend', 'xp_required': 2500, 'badge': '💎'},
    }
