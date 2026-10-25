"""
Quiz Master Pro - Question Routes
Question bank management for MCQ, True/False, and Short Answer questions
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
import json

questions_bp = Blueprint('questions', __name__)

def check_teacher_admin():
    """Check if user is teacher or admin"""
    role = session.get('role')
    return role in ['teacher', 'admin']

@questions_bp.route('/list/<int:quiz_id>', methods=['GET'])
def list_questions(quiz_id):
    """Get all questions for a quiz"""
    include_answers = request.args.get('include_answers', 'false') == 'true'
    
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
    
    for q in questions or []:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    return jsonify({'success': True, 'questions': questions or []})

@questions_bp.route('/all', methods=['GET'])
def list_all_questions():
    """Get all questions from all quizzes (for Question Bank)"""
    quiz_id = request.args.get('quiz_id')
    question_type = request.args.get('type')
    
    query = """
        SELECT q.*, z.title as quiz_title 
        FROM questions q
        JOIN quizzes z ON q.quiz_id = z.id
        WHERE 1=1
    """
    params = []
    
    if quiz_id:
        query += " AND q.quiz_id = %s"
        params.append(quiz_id)
        
    if question_type:
        query += " AND q.type = %s"
        params.append(question_type)
        
    query += " ORDER BY q.id DESC"
    
    questions = execute_query(query, tuple(params))
    
    # Parse JSON options
    for q in questions or []:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
                
    return jsonify({'success': True, 'questions': questions or []})

@questions_bp.route('/get/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get a single question"""
    questions = execute_query(
        "SELECT * FROM questions WHERE id = %s",
        (question_id,)
    )
    
    if not questions:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    
    question = questions[0]
    if question.get('options'):
        try:
            question['options'] = json.loads(question['options']) if isinstance(question['options'], str) else question['options']
        except:
            pass
    
    return jsonify({'success': True, 'question': question})

@questions_bp.route('/add', methods=['POST'])
def add_question():
    """Add a new question to a quiz"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    quiz_id = data.get('quiz_id')
    question_type = data.get('type', 'mcq')
    question_text = data.get('question_text', '').strip()
    options = data.get('options', [])
    correct_answer = data.get('correct_answer', '')
    explanation = data.get('explanation', '')
    points = data.get('points', 10)
    
    if not quiz_id or not question_text or not correct_answer:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Convert options to JSON string
    options_json = json.dumps(options) if options else None
    
    question_id = execute_query(
        """INSERT INTO questions (quiz_id, type, question_text, options, 
                                  correct_answer, explanation, points)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (quiz_id, question_type, question_text, options_json, 
         correct_answer, explanation, points),
        fetch=False
    )
    
    if question_id:
        return jsonify({
            'success': True,
            'message': 'Question added successfully!',
            'question_id': question_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to add question'}), 500

@questions_bp.route('/add-bulk', methods=['POST'])
def add_bulk_questions():
    """Add multiple questions at once"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    questions = data.get('questions', [])
    
    if not quiz_id or not questions:
        return jsonify({'success': False, 'message': 'Quiz ID and questions are required'}), 400
    
    added_count = 0
    
    for q in questions:
        options_json = json.dumps(q.get('options', [])) if q.get('options') else None
        
        question_id = execute_query(
            """INSERT INTO questions (quiz_id, type, question_text, options, 
                                      correct_answer, explanation, points)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (quiz_id, q.get('type', 'mcq'), q.get('question_text', ''),
             options_json, q.get('correct_answer', ''), 
             q.get('explanation', ''), q.get('points', 10)),
            fetch=False
        )
        
        if question_id:
            added_count += 1
    
    return jsonify({
        'success': True,
        'message': f'{added_count} questions added successfully!',
        'added_count': added_count
    })

@questions_bp.route('/update/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """Update a question"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    updates = []
    params = []
    
    if 'type' in data:
        updates.append("type = %s")
        params.append(data['type'])
    
    if 'question_text' in data:
        updates.append("question_text = %s")
        params.append(data['question_text'])
    
    if 'options' in data:
        updates.append("options = %s")
        params.append(json.dumps(data['options']))
    
    if 'correct_answer' in data:
        updates.append("correct_answer = %s")
        params.append(data['correct_answer'])
    
    if 'explanation' in data:
        updates.append("explanation = %s")
        params.append(data['explanation'])
    
    if 'points' in data:
        updates.append("points = %s")
        params.append(data['points'])
    
    if not updates:
        return jsonify({'success': False, 'message': 'No updates provided'}), 400
    
    params.append(question_id)
    
    execute_query(
        f"UPDATE questions SET {', '.join(updates)} WHERE id = %s",
        tuple(params),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'Question updated successfully!'})

@questions_bp.route('/delete/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Delete a question"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    execute_query("DELETE FROM questions WHERE id = %s", (question_id,), fetch=False)
    
    return jsonify({'success': True, 'message': 'Question deleted successfully!'})

@questions_bp.route('/check-answer', methods=['POST'])
def check_answer():
    """Check if an answer is correct"""
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer', '').strip().lower()
    
    questions = execute_query(
        "SELECT correct_answer, explanation, points FROM questions WHERE id = %s",
        (question_id,)
    )
    
    if not questions:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    
    question = questions[0]
    correct = question['correct_answer'].strip().lower()
    is_correct = user_answer == correct
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': question['correct_answer'],
        'explanation': question['explanation'],
        'points': question['points'] if is_correct else 0
    })
