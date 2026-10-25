"""
Quiz Master Pro - Practice Routes
Practice mode with progress tracking and retry functionality
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
import json
import random

practice_bp = Blueprint('practice', __name__)

@practice_bp.route('/categories', methods=['GET'])
def get_practice_categories():
    """Get categories with practice progress"""
    user_id = session.get('user_id')
    
    categories = execute_query("""
        SELECT c.*, 
               (SELECT COUNT(*) FROM quizzes WHERE category_id = c.id AND is_active = TRUE) as quiz_count,
               (SELECT COUNT(*) FROM questions q 
                JOIN quizzes qz ON q.quiz_id = qz.id 
                WHERE qz.category_id = c.id AND qz.is_active = TRUE) as total_questions
        FROM categories c
        ORDER BY c.name
    """) or []
    
    # Add user progress if logged in
    if user_id:
        for category in categories:
            progress = execute_query(
                """SELECT questions_attempted, correct_answers 
                   FROM practice_progress 
                   WHERE user_id = %s AND category_id = %s""",
                (user_id, category['id'])
            )
            
            if progress:
                category['questions_attempted'] = progress[0]['questions_attempted']
                category['correct_answers'] = progress[0]['correct_answers']
                if category['questions_attempted'] > 0:
                    category['accuracy'] = round(
                        (category['correct_answers'] / category['questions_attempted']) * 100, 1
                    )
                else:
                    category['accuracy'] = 0
            else:
                category['questions_attempted'] = 0
                category['correct_answers'] = 0
                category['accuracy'] = 0
    
    return jsonify({'success': True, 'categories': categories})

@practice_bp.route('/questions/<int:category_id>', methods=['GET'])
def get_practice_questions(category_id):
    """Get practice questions for a category"""
    difficulty = request.args.get('difficulty')
    limit = request.args.get('limit', 10, type=int)
    
    query = """
        SELECT q.id, q.type, q.question_text, q.options, q.points, q.explanation,
               qz.title as quiz_title, qz.difficulty
        FROM questions q
        JOIN quizzes qz ON q.quiz_id = qz.id
        WHERE qz.category_id = %s AND qz.is_active = TRUE
    """
    params = [category_id]
    
    if difficulty:
        query += " AND qz.difficulty = %s"
        params.append(difficulty)
    
    query += " ORDER BY RAND() LIMIT %s"
    params.append(limit)
    
    questions = execute_query(query, tuple(params)) or []
    
    for q in questions:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    return jsonify({'success': True, 'questions': questions})

@practice_bp.route('/submit-answer', methods=['POST'])
def submit_practice_answer():
    """Submit an answer in practice mode"""
    user_id = session.get('user_id')
    
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer', '').strip()
    category_id = data.get('category_id')
    
    # Get question and check answer
    questions = execute_query(
        "SELECT correct_answer, explanation, points FROM questions WHERE id = %s",
        (question_id,)
    )
    
    if not questions:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    
    question = questions[0]
    is_correct = answer.lower() == question['correct_answer'].lower()
    
    # Update progress if logged in
    if user_id and category_id:
        # Check if progress exists
        progress = execute_query(
            "SELECT id, wrong_questions FROM practice_progress WHERE user_id = %s AND category_id = %s",
            (user_id, category_id)
        )
        
        if progress:
            # Update existing progress
            wrong_questions = progress[0]['wrong_questions']
            if wrong_questions:
                try:
                    wrong_questions = json.loads(wrong_questions) if isinstance(wrong_questions, str) else wrong_questions
                except:
                    wrong_questions = []
            else:
                wrong_questions = []
            
            if is_correct:
                # Remove from wrong questions if it was there
                wrong_questions = [q for q in wrong_questions if q != question_id]
                execute_query(
                    """UPDATE practice_progress 
                       SET questions_attempted = questions_attempted + 1,
                           correct_answers = correct_answers + 1,
                           wrong_questions = %s
                       WHERE id = %s""",
                    (json.dumps(wrong_questions), progress[0]['id']),
                    fetch=False
                )
            else:
                # Add to wrong questions if not already there
                if question_id not in wrong_questions:
                    wrong_questions.append(question_id)
                execute_query(
                    """UPDATE practice_progress 
                       SET questions_attempted = questions_attempted + 1,
                           wrong_questions = %s
                       WHERE id = %s""",
                    (json.dumps(wrong_questions), progress[0]['id']),
                    fetch=False
                )
        else:
            # Create new progress
            wrong_questions = [] if is_correct else [question_id]
            execute_query(
                """INSERT INTO practice_progress 
                   (user_id, category_id, questions_attempted, correct_answers, wrong_questions)
                   VALUES (%s, %s, 1, %s, %s)""",
                (user_id, category_id, 1 if is_correct else 0, json.dumps(wrong_questions)),
                fetch=False
            )
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': question['correct_answer'],
        'explanation': question['explanation'],
        'points': question['points'] if is_correct else 0
    })

@practice_bp.route('/wrong-questions/<int:category_id>', methods=['GET'])
def get_wrong_questions(category_id):
    """Get questions that user got wrong for retry"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    progress = execute_query(
        "SELECT wrong_questions FROM practice_progress WHERE user_id = %s AND category_id = %s",
        (user_id, category_id)
    )
    
    if not progress or not progress[0]['wrong_questions']:
        return jsonify({'success': True, 'questions': []})
    
    wrong_ids = progress[0]['wrong_questions']
    if isinstance(wrong_ids, str):
        try:
            wrong_ids = json.loads(wrong_ids)
        except:
            wrong_ids = []
    
    if not wrong_ids:
        return jsonify({'success': True, 'questions': []})
    
    placeholders = ','.join(['%s'] * len(wrong_ids))
    questions = execute_query(
        f"""SELECT q.id, q.type, q.question_text, q.options, q.points, q.explanation
            FROM questions q
            WHERE q.id IN ({placeholders})""",
        tuple(wrong_ids)
    ) or []
    
    for q in questions:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    return jsonify({'success': True, 'questions': questions})

@practice_bp.route('/progress', methods=['GET'])
def get_overall_progress():
    """Get overall practice progress for user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    progress = execute_query(
        """SELECT pp.*, c.name as category_name, c.icon as category_icon
           FROM practice_progress pp
           JOIN categories c ON pp.category_id = c.id
           WHERE pp.user_id = %s""",
        (user_id,)
    ) or []
    
    total_attempted = sum(p['questions_attempted'] for p in progress)
    total_correct = sum(p['correct_answers'] for p in progress)
    overall_accuracy = round((total_correct / total_attempted) * 100, 1) if total_attempted > 0 else 0
    
    return jsonify({
        'success': True,
        'progress': progress,
        'summary': {
            'total_attempted': total_attempted,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'categories_practiced': len(progress)
        }
    })

@practice_bp.route('/reset/<int:category_id>', methods=['POST'])
def reset_progress(category_id):
    """Reset practice progress for a category"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    execute_query(
        "DELETE FROM practice_progress WHERE user_id = %s AND category_id = %s",
        (user_id, category_id),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'Progress reset successfully!'})
