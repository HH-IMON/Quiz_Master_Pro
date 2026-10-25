"""
Quiz Master Pro - Quiz Routes
CRUD operations for quizzes (Teacher/Admin only)
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
import json

quiz_bp = Blueprint('quiz', __name__)

def check_teacher_admin():
    """Check if user is teacher or admin"""
    role = session.get('role')
    return role in ['teacher', 'admin']

@quiz_bp.route('/list', methods=['GET'])
def list_quizzes():
    """Get all quizzes"""
    category_id = request.args.get('category_id')
    difficulty = request.args.get('difficulty')
    created_by = request.args.get('created_by')
    active_only = request.args.get('active_only', 'true') == 'true'
    
    query = """
        SELECT q.*, c.name as category_name, c.icon as category_icon,
               u.username as creator_name,
               (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count
        FROM quizzes q
        LEFT JOIN categories c ON q.category_id = c.id
        LEFT JOIN users u ON q.created_by = u.id
        WHERE 1=1
    """
    params = []
    
    if active_only:
        query += " AND q.is_active = TRUE"
    
    if category_id:
        query += " AND q.category_id = %s"
        params.append(category_id)
    
    if difficulty:
        query += " AND q.difficulty = %s"
        params.append(difficulty)
    
    if created_by:
        query += " AND q.created_by = %s"
        params.append(created_by)
    
    query += " ORDER BY q.created_at DESC"
    
    quizzes = execute_query(query, tuple(params)) or []
    
    for quiz in quizzes:
        if quiz.get('created_at'):
            quiz['created_at'] = quiz['created_at'].isoformat()
    
    return jsonify({'success': True, 'quizzes': quizzes})

@quiz_bp.route('/get/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get a single quiz with questions"""
    include_answers = request.args.get('include_answers', 'false') == 'true'
    
    quizzes = execute_query(
        """SELECT q.*, c.name as category_name, c.icon as category_icon,
                  u.username as creator_name
           FROM quizzes q
           LEFT JOIN categories c ON q.category_id = c.id
           LEFT JOIN users u ON q.created_by = u.id
           WHERE q.id = %s""",
        (quiz_id,)
    )
    
    if not quizzes:
        return jsonify({'success': False, 'message': 'Quiz not found'}), 404
    
    quiz = quizzes[0]
    if quiz.get('created_at'):
        quiz['created_at'] = quiz['created_at'].isoformat()
    
    # Get questions
    if include_answers:
        questions = execute_query(
            "SELECT * FROM questions WHERE quiz_id = %s ORDER BY id",
            (quiz_id,)
        )
    else:
        questions = execute_query(
            """SELECT id, quiz_id, type, question_text, options, points 
               FROM questions WHERE quiz_id = %s ORDER BY id""",
            (quiz_id,)
        )
    
    # Parse JSON options
    for q in questions or []:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    quiz['questions'] = questions or []
    
    return jsonify({'success': True, 'quiz': quiz})

@quiz_bp.route('/create', methods=['POST'])
def create_quiz():
    """Create a new quiz"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    title = data.get('title', '').strip()
    description = data.get('description', '')
    category_id = data.get('category_id')
    difficulty = data.get('difficulty', 'medium')
    time_per_question = data.get('time_per_question', 30)
    
    if not title:
        return jsonify({'success': False, 'message': 'Title is required'}), 400
    
    quiz_id = execute_query(
        """INSERT INTO quizzes (title, description, category_id, created_by, 
                                difficulty, time_per_question)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (title, description, category_id, session.get('user_id'), 
         difficulty, time_per_question),
        fetch=False
    )
    
    if quiz_id:
        return jsonify({
            'success': True,
            'message': 'Quiz created successfully!',
            'quiz_id': quiz_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to create quiz'}), 500

@quiz_bp.route('/update/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    """Update a quiz"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Build update query
    updates = []
    params = []
    
    if 'title' in data:
        updates.append("title = %s")
        params.append(data['title'])
    
    if 'description' in data:
        updates.append("description = %s")
        params.append(data['description'])
    
    if 'category_id' in data:
        updates.append("category_id = %s")
        params.append(data['category_id'])
    
    if 'difficulty' in data:
        updates.append("difficulty = %s")
        params.append(data['difficulty'])
    
    if 'time_per_question' in data:
        updates.append("time_per_question = %s")
        params.append(data['time_per_question'])
    
    if 'is_active' in data:
        updates.append("is_active = %s")
        params.append(data['is_active'])
    
    if not updates:
        return jsonify({'success': False, 'message': 'No updates provided'}), 400
    
    params.append(quiz_id)
    
    execute_query(
        f"UPDATE quizzes SET {', '.join(updates)} WHERE id = %s",
        tuple(params),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'Quiz updated successfully!'})

@quiz_bp.route('/delete/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """Delete a quiz"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if quiz exists and belongs to user (or user is admin)
    quizzes = execute_query(
        "SELECT created_by FROM quizzes WHERE id = %s",
        (quiz_id,)
    )
    
    if not quizzes:
        return jsonify({'success': False, 'message': 'Quiz not found'}), 404
    
    if session.get('role') != 'admin' and quizzes[0]['created_by'] != session.get('user_id'):
        return jsonify({'success': False, 'message': 'You can only delete your own quizzes'}), 403
    
    execute_query("DELETE FROM quizzes WHERE id = %s", (quiz_id,), fetch=False)
    
    return jsonify({'success': True, 'message': 'Quiz deleted successfully!'})

@quiz_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    categories = execute_query("SELECT * FROM categories ORDER BY name") or []
    return jsonify({'success': True, 'categories': categories})

@quiz_bp.route('/my-quizzes', methods=['GET'])
def my_quizzes():
    """Get quizzes created by current user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    quizzes = execute_query(
        """SELECT q.*, c.name as category_name, c.icon as category_icon,
                  (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count
           FROM quizzes q
           LEFT JOIN categories c ON q.category_id = c.id
           WHERE q.created_by = %s
           ORDER BY q.created_at DESC""",
        (user_id,)
    ) or []
    
    for quiz in quizzes:
        if quiz.get('created_at'):
            quiz['created_at'] = quiz['created_at'].isoformat()
    
    return jsonify({'success': True, 'quizzes': quizzes})
