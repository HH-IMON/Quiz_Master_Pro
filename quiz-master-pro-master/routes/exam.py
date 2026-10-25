"""
Quiz Master Pro - Exam Routes
Scheduled exam management for teachers/admins and exam taking for students
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
from datetime import datetime, timezone, timedelta
import json

# Bangladesh timezone (UTC+6)
BANGLADESH_TZ = timezone(timedelta(hours=6))

def parse_datetime_dhaka(dt_string):
    """Parse datetime string and convert to Bangladesh timezone"""
    if not dt_string:
        return None
    try:
        # Handle ISO format with Z suffix
        if dt_string.endswith('Z'):
            dt_string = dt_string[:-1] + '+00:00'
        # Parse ISO format
        dt = datetime.fromisoformat(dt_string)
        # If no timezone, assume Bangladesh
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BANGLADESH_TZ)
        return dt
    except ValueError:
        return None

exam_bp = Blueprint('exam', __name__)

def check_teacher_admin():
    """Check if user is teacher or admin"""
    role = session.get('role')
    return role in ['teacher', 'admin']

# ============================================
# EXAM MANAGEMENT (Teachers/Admins)
# ============================================

@exam_bp.route('/list', methods=['GET'])
def list_exams():
    """Get all exams"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    if user_role in ['teacher', 'admin']:
        # Teachers/Admins see their own exams
        if user_role == 'admin':
            # Admin sees all exams
            query = """
                SELECT e.*, q.title as quiz_title, u.username as creator_name,
                       (SELECT COUNT(*) FROM exam_submissions WHERE exam_id = e.id) as submission_count,
                       (SELECT COUNT(*) FROM questions WHERE quiz_id = e.quiz_id) as question_count
                FROM exams e
                LEFT JOIN quizzes q ON e.quiz_id = q.id
                LEFT JOIN users u ON e.created_by = u.id
                ORDER BY e.start_time DESC
            """
            exams = execute_query(query) or []
        else:
            query = """
                SELECT e.*, q.title as quiz_title, u.username as creator_name,
                       (SELECT COUNT(*) FROM exam_submissions WHERE exam_id = e.id) as submission_count,
                       (SELECT COUNT(*) FROM questions WHERE quiz_id = e.quiz_id) as question_count
                FROM exams e
                LEFT JOIN quizzes q ON e.quiz_id = q.id
                LEFT JOIN users u ON e.created_by = u.id
                WHERE e.created_by = %s
                ORDER BY e.start_time DESC
            """
            exams = execute_query(query, (user_id,)) or []
    else:
        # Students see only active exams within time window
        query = """
            SELECT e.id, e.title, e.description, e.start_time, e.end_time, 
                   e.duration_minutes, q.title as quiz_title,
                   (SELECT COUNT(*) FROM questions WHERE quiz_id = e.quiz_id) as question_count,
                   (SELECT status FROM exam_submissions WHERE exam_id = e.id AND user_id = %s) as my_status
            FROM exams e
            LEFT JOIN quizzes q ON e.quiz_id = q.id
            WHERE e.is_active = TRUE
            ORDER BY e.start_time ASC
        """
        exams = execute_query(query, (user_id,)) or []
    
    # Format datetime fields
    for exam in exams:
        if exam.get('start_time'):
            exam['start_time'] = exam['start_time'].isoformat()
        if exam.get('end_time'):
            exam['end_time'] = exam['end_time'].isoformat()
        if exam.get('created_at'):
            exam['created_at'] = exam['created_at'].isoformat()
    
    return jsonify({'success': True, 'exams': exams})

@exam_bp.route('/get/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    """Get exam details"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    exam = execute_query(
        """SELECT e.*, q.title as quiz_title, q.time_per_question,
                  u.username as creator_name,
                  (SELECT COUNT(*) FROM questions WHERE quiz_id = e.quiz_id) as question_count
           FROM exams e
           LEFT JOIN quizzes q ON e.quiz_id = q.id
           LEFT JOIN users u ON e.created_by = u.id
           WHERE e.id = %s""",
        (exam_id,)
    )
    
    if not exam:
        return jsonify({'success': False, 'message': 'Exam not found'}), 404
    
    exam = exam[0]
    
    # Format datetime fields
    if exam.get('start_time'):
        exam['start_time'] = exam['start_time'].isoformat()
    if exam.get('end_time'):
        exam['end_time'] = exam['end_time'].isoformat()
    if exam.get('created_at'):
        exam['created_at'] = exam['created_at'].isoformat()
    
    # Get submissions if teacher/admin
    if user_role in ['teacher', 'admin']:
        submissions = execute_query(
            """SELECT es.*, u.username, u.avatar
               FROM exam_submissions es
               JOIN users u ON es.user_id = u.id
               WHERE es.exam_id = %s
               ORDER BY es.score DESC""",
            (exam_id,)
        ) or []
        
        for sub in submissions:
            if sub.get('started_at'):
                sub['started_at'] = sub['started_at'].isoformat()
            if sub.get('submitted_at'):
                sub['submitted_at'] = sub['submitted_at'].isoformat()
        
        exam['submissions'] = submissions
    
    return jsonify({'success': True, 'exam': exam})

@exam_bp.route('/create', methods=['POST'])
def create_exam():
    """Create a new exam"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    title = data.get('title', '').strip()
    description = data.get('description', '')
    quiz_id = data.get('quiz_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    duration_minutes = data.get('duration_minutes', 60)
    show_results = data.get('show_results', True)
    
    if not title:
        return jsonify({'success': False, 'message': 'Title is required'}), 400
    
    if not quiz_id:
        return jsonify({'success': False, 'message': 'Quiz is required'}), 400
    
    if not start_time or not end_time:
        return jsonify({'success': False, 'message': 'Start and end times are required'}), 400
    
    # Parse datetime strings with Bangladesh timezone
    start_dt = parse_datetime_dhaka(start_time)
    end_dt = parse_datetime_dhaka(end_time)
    
    if not start_dt or not end_dt:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    if end_dt <= start_dt:
        return jsonify({'success': False, 'message': 'End time must be after start time'}), 400
    
    exam_id = execute_query(
        """INSERT INTO exams (title, description, quiz_id, created_by, 
                              start_time, end_time, duration_minutes, show_results)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (title, description, quiz_id, session.get('user_id'),
         start_dt, end_dt, duration_minutes, show_results),
        fetch=False
    )
    
    if exam_id:
        return jsonify({
            'success': True,
            'message': 'Exam scheduled successfully!',
            'exam_id': exam_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to create exam'}), 500

@exam_bp.route('/update/<int:exam_id>', methods=['PUT'])
def update_exam(exam_id):
    """Update an exam"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    
    updates = []
    params = []
    
    if 'title' in data:
        updates.append("title = %s")
        params.append(data['title'])
    
    if 'description' in data:
        updates.append("description = %s")
        params.append(data['description'])
    
    if 'start_time' in data:
        updates.append("start_time = %s")
        params.append(datetime.fromisoformat(data['start_time'].replace('Z', '+06:00')))
    
    if 'end_time' in data:
        updates.append("end_time = %s")
        params.append(datetime.fromisoformat(data['end_time'].replace('Z', '+06:00')))
    
    if 'duration_minutes' in data:
        updates.append("duration_minutes = %s")
        params.append(data['duration_minutes'])
    
    if 'is_active' in data:
        updates.append("is_active = %s")
        params.append(data['is_active'])
    
    if 'show_results' in data:
        updates.append("show_results = %s")
        params.append(data['show_results'])
    
    if not updates:
        return jsonify({'success': False, 'message': 'No updates provided'}), 400
    
    params.append(exam_id)
    
    execute_query(
        f"UPDATE exams SET {', '.join(updates)} WHERE id = %s",
        tuple(params),
        fetch=False
    )
    
    return jsonify({'success': True, 'message': 'Exam updated successfully!'})

@exam_bp.route('/delete/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    """Delete an exam"""
    if not check_teacher_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if exam exists and belongs to user (or user is admin)
    exams = execute_query("SELECT created_by FROM exams WHERE id = %s", (exam_id,))
    
    if not exams:
        return jsonify({'success': False, 'message': 'Exam not found'}), 404
    
    if session.get('role') != 'admin' and exams[0]['created_by'] != session.get('user_id'):
        return jsonify({'success': False, 'message': 'You can only delete your own exams'}), 403
    
    execute_query("DELETE FROM exams WHERE id = %s", (exam_id,), fetch=False)
    
    return jsonify({'success': True, 'message': 'Exam deleted successfully!'})

# ============================================
# EXAM TAKING (Students)
# ============================================

@exam_bp.route('/available', methods=['GET'])
def available_exams():
    """Get available exams for students"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    now = datetime.now()
    
    # Get exams that are currently available
    exams = execute_query(
        """SELECT e.id, e.title, e.description, e.start_time, e.end_time, 
                  e.duration_minutes, q.title as quiz_title,
                  (SELECT COUNT(*) FROM questions WHERE quiz_id = e.quiz_id) as question_count,
                  (SELECT status FROM exam_submissions WHERE exam_id = e.id AND user_id = %s) as my_status
           FROM exams e
           LEFT JOIN quizzes q ON e.quiz_id = q.id
           WHERE e.is_active = TRUE 
             AND e.start_time <= %s 
             AND e.end_time >= %s
           ORDER BY e.end_time ASC""",
        (user_id, now, now)
    ) or []
    
    # Get upcoming exams
    upcoming = execute_query(
        """SELECT e.id, e.title, e.description, e.start_time, e.end_time, 
                  e.duration_minutes, q.title as quiz_title,
                  (SELECT COUNT(*) FROM questions WHERE quiz_id = e.quiz_id) as question_count
           FROM exams e
           LEFT JOIN quizzes q ON e.quiz_id = q.id
           WHERE e.is_active = TRUE 
             AND e.start_time > %s
           ORDER BY e.start_time ASC
           LIMIT 5""",
        (now,)
    ) or []
    
    # Format datetime fields
    for exam in exams + upcoming:
        if exam.get('start_time'):
            exam['start_time'] = exam['start_time'].isoformat()
        if exam.get('end_time'):
            exam['end_time'] = exam['end_time'].isoformat()
    
    return jsonify({
        'success': True,
        'available': exams,
        'upcoming': upcoming
    })

@exam_bp.route('/start/<int:exam_id>', methods=['POST'])
def start_exam(exam_id):
    """Start taking an exam"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    # Check if exam exists and is available
    now = datetime.now()
    exams = execute_query(
        """SELECT e.*, q.time_per_question
           FROM exams e
           LEFT JOIN quizzes q ON e.quiz_id = q.id
           WHERE e.id = %s AND e.is_active = TRUE 
             AND e.start_time <= %s AND e.end_time >= %s""",
        (exam_id, now, now)
    )
    
    if not exams:
        return jsonify({'success': False, 'message': 'Exam not available'}), 404
    
    exam = exams[0]
    
    # Check if already started or submitted
    existing = execute_query(
        "SELECT * FROM exam_submissions WHERE exam_id = %s AND user_id = %s",
        (exam_id, user_id)
    )
    
    if existing:
        if existing[0]['status'] == 'submitted':
            return jsonify({'success': False, 'message': 'You have already submitted this exam'}), 400
        
        # Resume in-progress exam
        submission = existing[0]
    else:
        # Create new submission
        submission_id = execute_query(
            """INSERT INTO exam_submissions (exam_id, user_id, status)
               VALUES (%s, %s, 'in_progress')""",
            (exam_id, user_id),
            fetch=False
        )
        submission = {'id': submission_id, 'started_at': now}
    
    # Get questions (without correct answers)
    questions = execute_query(
        """SELECT id, type, question_text, options, points 
           FROM questions WHERE quiz_id = %s ORDER BY id""",
        (exam['quiz_id'],)
    ) or []
    
    # Parse options
    for q in questions:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    return jsonify({
        'success': True,
        'exam': {
            'id': exam['id'],
            'title': exam['title'],
            'duration_minutes': exam['duration_minutes'],
            'time_per_question': exam['time_per_question']
        },
        'questions': questions,
        'started_at': submission.get('started_at', now).isoformat() if hasattr(submission.get('started_at', now), 'isoformat') else str(submission.get('started_at', now))
    })

@exam_bp.route('/submit', methods=['POST'])
def submit_exam():
    """Submit exam answers"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    exam_id = data.get('exam_id')
    answers = data.get('answers', {})  # {question_id: answer}
    
    if not exam_id:
        return jsonify({'success': False, 'message': 'Exam ID is required'}), 400
    
    # Get submission
    submissions = execute_query(
        "SELECT * FROM exam_submissions WHERE exam_id = %s AND user_id = %s",
        (exam_id, user_id)
    )
    
    if not submissions:
        return jsonify({'success': False, 'message': 'Exam not started'}), 400
    
    submission = submissions[0]
    
    if submission['status'] == 'submitted':
        return jsonify({'success': False, 'message': 'Exam already submitted'}), 400
    
    # Get exam and calculate score
    exams = execute_query(
        "SELECT quiz_id FROM exams WHERE id = %s",
        (exam_id,)
    )
    
    if not exams:
        return jsonify({'success': False, 'message': 'Exam not found'}), 404
    
    quiz_id = exams[0]['quiz_id']
    
    # Get questions with correct answers
    questions = execute_query(
        "SELECT id, correct_answer, points FROM questions WHERE quiz_id = %s",
        (quiz_id,)
    ) or []
    
    total_questions = len(questions)
    correct_count = 0
    total_score = 0
    
    for q in questions:
        q_id = str(q['id'])
        if q_id in answers:
            student_answer = str(answers[q_id]).strip().lower()
            correct_answer = str(q['correct_answer']).strip().lower()
            
            if student_answer == correct_answer:
                correct_count += 1
                total_score += q['points']
    
    # Update submission
    execute_query(
        """UPDATE exam_submissions 
           SET answers = %s, score = %s, total_questions = %s, 
               correct_answers = %s, submitted_at = NOW(), status = 'submitted'
           WHERE id = %s""",
        (json.dumps(answers), total_score, total_questions, correct_count, submission['id']),
        fetch=False
    )
    
    # Check if results should be shown
    exam_info = execute_query("SELECT show_results FROM exams WHERE id = %s", (exam_id,))
    show_results = exam_info[0]['show_results'] if exam_info else True
    
    result = {
        'success': True,
        'message': 'Exam submitted successfully!'
    }
    
    if show_results:
        result['score'] = total_score
        result['total_questions'] = total_questions
        result['correct_answers'] = correct_count
        result['percentage'] = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
    
    return jsonify(result)

@exam_bp.route('/my-results', methods=['GET'])
def my_exam_results():
    """Get student's exam results"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    results = execute_query(
        """SELECT es.*, e.title as exam_title, e.show_results
           FROM exam_submissions es
           JOIN exams e ON es.exam_id = e.id
           WHERE es.user_id = %s AND es.status = 'submitted'
           ORDER BY es.submitted_at DESC""",
        (user_id,)
    ) or []
    
    for r in results:
        if r.get('started_at'):
            r['started_at'] = r['started_at'].isoformat()
        if r.get('submitted_at'):
            r['submitted_at'] = r['submitted_at'].isoformat()
        # Hide score if show_results is False
        if not r.get('show_results'):
            r['score'] = None
            r['correct_answers'] = None
    
    return jsonify({'success': True, 'results': results})
