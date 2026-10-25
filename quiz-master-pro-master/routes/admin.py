"""
Quiz Master Pro - Admin Routes
Platform administration and analytics
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

def check_admin():
    """Check if current user is admin"""
    return session.get('role') == 'admin'

@admin_bp.route('/stats', methods=['GET'])
def get_platform_stats():
    """Get platform statistics"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # User stats
    user_stats = execute_query("""
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN role = 'student' THEN 1 ELSE 0 END) as students,
            SUM(CASE WHEN role = 'teacher' THEN 1 ELSE 0 END) as teachers,
            SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admins,
            SUM(CASE WHEN is_online = TRUE THEN 1 ELSE 0 END) as online_users
        FROM users
    """)
    
    # Quiz stats
    quiz_stats = execute_query("""
        SELECT 
            COUNT(*) as total_quizzes,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_quizzes
        FROM quizzes
    """)
    
    # Question stats
    question_stats = execute_query("""
        SELECT 
            COUNT(*) as total_questions,
            SUM(CASE WHEN type = 'mcq' THEN 1 ELSE 0 END) as mcq_questions,
            SUM(CASE WHEN type = 'truefalse' THEN 1 ELSE 0 END) as truefalse_questions,
            SUM(CASE WHEN type = 'short' THEN 1 ELSE 0 END) as short_questions
        FROM questions
    """)
    
    # Game stats
    game_stats = execute_query("""
        SELECT 
            COUNT(*) as total_games,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_games
        FROM game_rooms
    """)
    
    # Battle stats
    battle_stats = execute_query("""
        SELECT COUNT(*) as total_battles FROM battle_matches WHERE status = 'completed'
    """)
    
    # Recent activity
    recent_users = execute_query("""
        SELECT id, username, email, role, created_at 
        FROM users ORDER BY created_at DESC LIMIT 5
    """) or []
    
    for user in recent_users:
        if user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
    
    return jsonify({
        'success': True,
        'stats': {
            'users': user_stats[0] if user_stats else {},
            'quizzes': quiz_stats[0] if quiz_stats else {},
            'questions': question_stats[0] if question_stats else {},
            'games': game_stats[0] if game_stats else {},
            'battles': battle_stats[0] if battle_stats else {},
            'recent_users': recent_users
        }
    })

@admin_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    role = request.args.get('role')
    search = request.args.get('search', '')
    
    query = """
        SELECT id, username, email, role, avatar, xp_points, level, rank_badge,
               is_online, last_seen, created_at
        FROM users WHERE 1=1
    """
    params = []
    
    if role:
        query += " AND role = %s"
        params.append(role)
    
    if search:
        query += " AND (username LIKE %s OR email LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY created_at DESC"
    
    users = execute_query(query, tuple(params) if params else None) or []
    
    for user in users:
        if user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
        if user.get('last_seen'):
            user['last_seen'] = user['last_seen'].isoformat()
    
    return jsonify({'success': True, 'users': users})

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    users = execute_query(
        """SELECT id, username, email, role, avatar, xp_points, level, rank_badge,
                  is_online, last_seen, created_at
           FROM users WHERE id = %s""",
        (user_id,)
    )
    
    if not users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user = users[0]
    
    # Get user stats
    quiz_results = execute_query(
        """SELECT COUNT(*) as quizzes_taken, 
                  AVG(score) as avg_score
           FROM quiz_results WHERE user_id = %s""",
        (user_id,)
    )
    
    battle_stats = execute_query(
        """SELECT 
              COUNT(*) as total_battles,
              SUM(CASE WHEN winner_id = %s THEN 1 ELSE 0 END) as wins
           FROM battle_matches
           WHERE (player1_id = %s OR player2_id = %s) AND status = 'completed'""",
        (user_id, user_id, user_id)
    )
    
    user['quiz_stats'] = quiz_results[0] if quiz_results else {}
    user['battle_stats'] = battle_stats[0] if battle_stats else {}
    
    if user.get('created_at'):
        user['created_at'] = user['created_at'].isoformat()
    if user.get('last_seen'):
        user['last_seen'] = user['last_seen'].isoformat()
    
    return jsonify({'success': True, 'user': user})

@admin_bp.route('/users/create', methods=['POST'])
def create_user():
    """Create a new user"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'student')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    # Check if exists
    existing = execute_query(
        "SELECT id FROM users WHERE username = %s OR email = %s",
        (username, email)
    )
    
    if existing:
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    
    password_hash = generate_password_hash(password)
    
    user_id = execute_query(
        "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (username, email, password_hash, role),
        fetch=False
    )
    
    if user_id:
        return jsonify({
            'success': True,
            'message': 'User created successfully!',
            'user_id': user_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to create user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user details"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    updates = []
    params = []
    
    if 'username' in data:
        updates.append("username = %s")
        params.append(data['username'])
    
    if 'email' in data:
        updates.append("email = %s")
        params.append(data['email'])
    
    if 'role' in data:
        updates.append("role = %s")
        params.append(data['role'])
    
    if 'password' in data and data['password']:
        updates.append("password_hash = %s")
        params.append(generate_password_hash(data['password']))
    
    if 'xp_points' in data:
        updates.append("xp_points = %s")
        params.append(data['xp_points'])
    
    if 'level' in data:
        updates.append("level = %s")
        params.append(data['level'])
    
    if not updates:
        return jsonify({'success': False, 'message': 'No updates provided'}), 400
    
    params.append(user_id)
    
    execute_query(
        f"UPDATE users SET {', '.join(updates)} WHERE id = %s",
        tuple(params),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'User updated successfully!'})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Don't allow deleting self
    if user_id == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Cannot delete yourself'}), 400
    
    execute_query("DELETE FROM users WHERE id = %s", (user_id,), fetch=False)
    
    return jsonify({'success': True, 'message': 'User deleted successfully!'})

@admin_bp.route('/quizzes', methods=['GET'])
def get_all_quizzes():
    """Get all quizzes for admin"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    quizzes = execute_query("""
        SELECT q.*, c.name as category_name, u.username as creator_name,
               (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count,
               (SELECT COUNT(*) FROM quiz_results WHERE quiz_id = q.id) as times_played
        FROM quizzes q
        LEFT JOIN categories c ON q.category_id = c.id
        LEFT JOIN users u ON q.created_by = u.id
        ORDER BY q.created_at DESC
    """) or []
    
    for quiz in quizzes:
        if quiz.get('created_at'):
            quiz['created_at'] = quiz['created_at'].isoformat()
    
    return jsonify({'success': True, 'quizzes': quizzes})

@admin_bp.route('/quizzes/<int:quiz_id>/toggle', methods=['POST'])
def toggle_quiz_status(quiz_id):
    """Toggle quiz active status"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    execute_query(
        "UPDATE quizzes SET is_active = NOT is_active WHERE id = %s",
        (quiz_id,),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'Quiz status updated!'})

@admin_bp.route('/analytics/daily', methods=['GET'])
def get_daily_analytics():
    """Get daily analytics for charts"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # New users per day (last 7 days)
    new_users = execute_query("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM users
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date
    """) or []
    
    # Quizzes played per day
    quizzes_played = execute_query("""
        SELECT DATE(completed_at) as date, COUNT(*) as count
        FROM quiz_results
        WHERE completed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(completed_at)
        ORDER BY date
    """) or []
    
    # Battles per day
    battles = execute_query("""
        SELECT DATE(match_time) as date, COUNT(*) as count
        FROM battle_matches
        WHERE match_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND status = 'completed'
        GROUP BY DATE(match_time)
        ORDER BY date
    """) or []
    
    for item in new_users + quizzes_played + battles:
        if item.get('date'):
            item['date'] = item['date'].isoformat()
    
    return jsonify({
        'success': True,
        'analytics': {
            'new_users': new_users,
            'quizzes_played': quizzes_played,
            'battles': battles
        }
    })

@admin_bp.route('/leaderboard', methods=['GET'])
def get_global_leaderboard():
    """Get global leaderboard"""
    limit = request.args.get('limit', 20, type=int)
    
    users = execute_query("""
        SELECT id, username, avatar, xp_points, level, rank_badge
        FROM users
        WHERE role = 'student'
        ORDER BY xp_points DESC
        LIMIT %s
    """, (limit,)) or []
    
    for i, user in enumerate(users):
        user['position'] = i + 1
    
    return jsonify({'success': True, 'leaderboard': users})

# ============================================
# CATEGORIES MANAGEMENT
# ============================================

@admin_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    categories = execute_query("""
        SELECT c.*, 
               (SELECT COUNT(*) FROM quizzes WHERE category_id = c.id) as quiz_count
        FROM categories c
        ORDER BY c.name
    """) or []
    
    return jsonify({'success': True, 'categories': categories})

@admin_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a new category"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '')
    icon = data.get('icon', '📚')
    color = data.get('color', '#667eea')
    
    if not name:
        return jsonify({'success': False, 'message': 'Category name is required'}), 400
    
    # Check if category already exists
    existing = execute_query(
        "SELECT id FROM categories WHERE name = %s",
        (name,)
    )
    
    if existing:
        return jsonify({'success': False, 'message': 'Category already exists'}), 400
    
    category_id = execute_query(
        """INSERT INTO categories (name, description, icon, color)
           VALUES (%s, %s, %s, %s)""",
        (name, description, icon, color),
        fetch=False
    )
    
    if category_id:
        return jsonify({
            'success': True,
            'message': 'Category created successfully!',
            'category_id': category_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to create category'}), 500

@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a category"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    updates = []
    params = []
    
    if 'name' in data:
        updates.append("name = %s")
        params.append(data['name'])
    
    if 'description' in data:
        updates.append("description = %s")
        params.append(data['description'])
    
    if 'icon' in data:
        updates.append("icon = %s")
        params.append(data['icon'])
    
    if 'color' in data:
        updates.append("color = %s")
        params.append(data['color'])
    
    if not updates:
        return jsonify({'success': False, 'message': 'No updates provided'}), 400
    
    params.append(category_id)
    
    execute_query(
        f"UPDATE categories SET {', '.join(updates)} WHERE id = %s",
        tuple(params),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'Category updated successfully!'})

@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    if not check_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if category has quizzes
    quizzes = execute_query(
        "SELECT COUNT(*) as count FROM quizzes WHERE category_id = %s",
        (category_id,)
    )
    
    if quizzes and quizzes[0]['count'] > 0:
        return jsonify({
            'success': False, 
            'message': f"Cannot delete category with {quizzes[0]['count']} quizzes. Move or delete quizzes first."
        }), 400
    
    execute_query("DELETE FROM categories WHERE id = %s", (category_id,), fetch=False)
    
    return jsonify({'success': True, 'message': 'Category deleted successfully!'})

