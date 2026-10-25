"""
Quiz Master Pro - Authentication Routes
Handle user registration, login, logout, and session management
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import execute_query
from config import Config
import json

auth_bp = Blueprint('auth', __name__)

def get_level_info(xp):
    """Get level and badge based on XP"""
    level = 1
    badge = '🌱'
    
    for lvl, info in sorted(Config.LEVELS.items(), reverse=True):
        if xp >= info['xp_required']:
            level = lvl
            badge = info['badge']
            break
    
    return level, badge

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'student')
    avatar = data.get('avatar', 'avatar1')
    
    # Validation
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if len(username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    # Check if username or email exists
    existing = execute_query(
        "SELECT id FROM users WHERE username = %s OR email = %s",
        (username, email)
    )
    
    if existing:
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    
    # Create user
    password_hash = generate_password_hash(password)
    
    user_id = execute_query(
        """INSERT INTO users (username, email, password_hash, role, avatar) 
           VALUES (%s, %s, %s, %s, %s)""",
        (username, email, password_hash, role, avatar),
        fetch=False
    )
    
    if user_id:
        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'user_id': user_id
        })
    
    return jsonify({'success': False, 'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    portal = data.get('portal', 'client')  # 'client' or 'server'
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    # Find user
    users = execute_query(
        """SELECT id, username, email, password_hash, role, avatar, 
                  xp_points, level, rank_badge 
           FROM users WHERE username = %s OR email = %s""",
        (username, username)
    )
    
    if not users:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    user = users[0]
    
    # Verify password
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    # Check portal access
    if portal == 'server' and user['role'] not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'Access denied. Only admins and teachers can access server portal.'}), 403
    
    if portal == 'client' and user['role'] != 'student':
        return jsonify({'success': False, 'message': 'Please use the server portal for admin/teacher access.'}), 403
    
    # Update online status
    execute_query(
        "UPDATE users SET is_online = TRUE, last_seen = NOW() WHERE id = %s",
        (user['id'],),
        fetch=False
    )
    
    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['avatar'] = user['avatar']
    
    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'avatar': user['avatar'],
            'xp_points': user['xp_points'],
            'level': user['level'],
            'rank_badge': user['rank_badge']
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout current user"""
    user_id = session.get('user_id')
    
    if user_id:
        execute_query(
            "UPDATE users SET is_online = FALSE, last_seen = NOW() WHERE id = %s",
            (user_id,),
            fetch=False
        )
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current logged in user info"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    users = execute_query(
        """SELECT id, username, email, role, avatar, xp_points, level, rank_badge,
                  created_at
           FROM users WHERE id = %s""",
        (user_id,)
    )
    
    if not users:
        session.clear()
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user = users[0]
    user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
    
    return jsonify({
        'success': True,
        'user': user
    })

@auth_bp.route('/update-profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    avatar = data.get('avatar')
    
    if avatar:
        execute_query(
            "UPDATE users SET avatar = %s WHERE id = %s",
            (avatar, user_id),
            fetch=False
        )
        session['avatar'] = avatar
    
    return jsonify({'success': True, 'message': 'Profile updated'})

@auth_bp.route('/add-xp', methods=['POST'])
def add_xp():
    """Add XP points to user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    xp_to_add = data.get('xp', 0)
    
    # Get current XP
    users = execute_query(
        "SELECT xp_points FROM users WHERE id = %s",
        (user_id,)
    )
    
    if not users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    new_xp = users[0]['xp_points'] + xp_to_add
    level, badge = get_level_info(new_xp)
    
    execute_query(
        "UPDATE users SET xp_points = %s, level = %s, rank_badge = %s WHERE id = %s",
        (new_xp, level, badge, user_id),
        fetch=False
    )
    
    return jsonify({
        'success': True,
        'xp_points': new_xp,
        'level': level,
        'rank_badge': badge,
        'level_name': Config.LEVELS[level]['name']
    })
