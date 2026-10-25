"""
Quiz Master Pro - Game Routes
Live game room management for Kahoot-style quizzes
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
import random
import string
import json

game_bp = Blueprint('game', __name__)

def generate_room_code():
    """Generate a unique 6-character room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        existing = execute_query(
            "SELECT id FROM game_rooms WHERE room_code = %s AND status != 'ended'",
            (code,)
        )
        if not existing:
            return code

@game_bp.route('/create-room', methods=['POST'])
def create_room():
    """Create a new game room"""
    if session.get('role') not in ['teacher', 'admin']:
        return jsonify({'success': False, 'message': 'Only teachers can create game rooms'}), 403
    
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    
    if not quiz_id:
        return jsonify({'success': False, 'message': 'Quiz ID is required'}), 400
    
    # Check if quiz exists and has questions
    quizzes = execute_query(
        """SELECT q.*, (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count
           FROM quizzes q WHERE q.id = %s""",
        (quiz_id,)
    )
    
    if not quizzes:
        return jsonify({'success': False, 'message': 'Quiz not found'}), 404
    
    if quizzes[0]['question_count'] == 0:
        return jsonify({'success': False, 'message': 'Quiz has no questions'}), 400
    
    room_code = generate_room_code()
    
    room_id = execute_query(
        """INSERT INTO game_rooms (room_code, quiz_id, host_id, status)
           VALUES (%s, %s, %s, 'waiting')""",
        (room_code, quiz_id, session.get('user_id')),
        fetch=False
    )
    
    if room_id:
        return jsonify({
            'success': True,
            'message': 'Game room created!',
            'room_code': room_code,
            'room_id': room_id,
            'quiz': quizzes[0]
        })
    
    return jsonify({'success': False, 'message': 'Failed to create room'}), 500

@game_bp.route('/join-room', methods=['POST'])
def join_room():
    """Join a game room - Students only"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    # Prevent admin/teacher from joining as participants
    if user_role in ['admin', 'teacher']:
        return jsonify({
            'success': False, 
            'message': 'Teachers and admins cannot join as players. Use "Host Game" instead.'
        }), 403
    
    data = request.get_json()
    room_code = data.get('room_code', '').strip().upper()
    
    if not room_code:
        return jsonify({'success': False, 'message': 'Room code is required'}), 400
    
    # Find room
    rooms = execute_query(
        """SELECT gr.*, q.title as quiz_title, q.time_per_question,
                  u.username as host_name
           FROM game_rooms gr
           JOIN quizzes q ON gr.quiz_id = q.id
           JOIN users u ON gr.host_id = u.id
           WHERE gr.room_code = %s AND gr.status IN ('waiting', 'active')""",
        (room_code,)
    )
    
    if not rooms:
        return jsonify({'success': False, 'message': 'Room not found or game has ended'}), 404
    
    room = rooms[0]
    
    # Check if already joined
    existing = execute_query(
        "SELECT id FROM game_participants WHERE room_id = %s AND user_id = %s",
        (room['id'], user_id)
    )
    
    if not existing:
        execute_query(
            "INSERT INTO game_participants (room_id, user_id) VALUES (%s, %s)",
            (room['id'], user_id),
            fetch=False
        )
    
    # Get participant count
    participants = execute_query(
        """SELECT gp.*, u.username, u.avatar 
           FROM game_participants gp
           JOIN users u ON gp.user_id = u.id
           WHERE gp.room_id = %s""",
        (room['id'],)
    ) or []
    
    return jsonify({
        'success': True,
        'message': 'Joined room successfully!',
        'room': {
            'id': room['id'],
            'room_code': room['room_code'],
            'quiz_title': room['quiz_title'],
            'time_per_question': room['time_per_question'],
            'host_name': room['host_name'],
            'status': room['status']
        },
        'participants': participants,
        'participant_count': len(participants)
    })

@game_bp.route('/room/<room_code>', methods=['GET'])
def get_room(room_code):
    """Get room details"""
    rooms = execute_query(
        """SELECT gr.*, q.title as quiz_title, q.time_per_question, q.description,
                  u.username as host_name,
                  (SELECT COUNT(*) FROM questions WHERE quiz_id = gr.quiz_id) as question_count
           FROM game_rooms gr
           JOIN quizzes q ON gr.quiz_id = q.id
           JOIN users u ON gr.host_id = u.id
           WHERE gr.room_code = %s""",
        (room_code.upper(),)
    )
    
    if not rooms:
        return jsonify({'success': False, 'message': 'Room not found'}), 404
    
    room = rooms[0]
    
    # Get participants
    participants = execute_query(
        """SELECT gp.score, gp.streak, u.username, u.avatar 
           FROM game_participants gp
           JOIN users u ON gp.user_id = u.id
           WHERE gp.room_id = %s
           ORDER BY gp.score DESC""",
        (room['id'],)
    ) or []
    
    if room.get('started_at'):
        room['started_at'] = room['started_at'].isoformat()
    if room.get('created_at'):
        room['created_at'] = room['created_at'].isoformat()
    
    return jsonify({
        'success': True,
        'room': room,
        'participants': participants
    })

@game_bp.route('/start/<room_code>', methods=['POST'])
def start_game(room_code):
    """Start the game (host only)"""
    try:
        user_id = session.get('user_id')
        print(f"DEBUG: start_game called for room {room_code} by user {user_id}")
        
        rooms = execute_query(
            "SELECT * FROM game_rooms WHERE room_code = %s AND host_id = %s",
            (room_code.upper(), user_id)
        )
        print(f"DEBUG: Room fetch result: {rooms}")
        
        if not rooms:
            print("DEBUG: Room not found or not host")
            return jsonify({'success': False, 'message': 'Room not found or you are not the host'}), 403
        
        execute_query(
            "UPDATE game_rooms SET status = 'active', started_at = NOW() WHERE id = %s",
            (rooms[0]['id'],),
            fetch=False
        )
        print("DEBUG: Room status updated to active")
        
        # Fetch questions for the host (including correct answers)
        questions = execute_query(
            """SELECT id, type, question_text, options, points, correct_answer 
               FROM questions WHERE quiz_id = %s ORDER BY id""",
            (rooms[0]['quiz_id'],)
        ) or []
        print(f"DEBUG: Fetched {len(questions)} questions")
        
        # Parse options
        for q in questions:
            if q.get('options'):
                try:
                    q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
                except Exception as parse_err:
                    print(f"DEBUG: Error parsing options for Q {q.get('id')}: {parse_err}")
                    pass
        
        response = {'success': True, 'message': 'Game started!', 'questions': questions}
        print("DEBUG: Returning success response")
        return jsonify(response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error starting game: {e}")
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500

@game_bp.route('/questions/<room_code>', methods=['GET'])
def get_game_questions(room_code):
    """Get questions for the game"""
    rooms = execute_query(
        "SELECT quiz_id FROM game_rooms WHERE room_code = %s",
        (room_code.upper(),)
    )
    
    if not rooms:
        return jsonify({'success': False, 'message': 'Room not found'}), 404
    
    questions = execute_query(
        """SELECT id, type, question_text, options, points 
           FROM questions WHERE quiz_id = %s ORDER BY id""",
        (rooms[0]['quiz_id'],)
    ) or []
    
    for q in questions:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    return jsonify({'success': True, 'questions': questions})

@game_bp.route('/submit-answer', methods=['POST'])
def submit_answer():
    """Submit an answer during the game"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    question_id = data.get('question_id')
    answer = data.get('answer', '').strip()
    time_taken = data.get('time_taken', 0)  # Time taken in seconds
    
    # Get room and verify participation
    rooms = execute_query(
        """SELECT gr.id, gr.quiz_id, q.time_per_question
           FROM game_rooms gr
           JOIN quizzes q ON gr.quiz_id = q.id
           WHERE gr.room_code = %s AND gr.status = 'active'""",
        (room_code,)
    )
    
    if not rooms:
        return jsonify({'success': False, 'message': 'Game not active'}), 400
    
    room = rooms[0]
    
    # Check answer
    questions = execute_query(
        "SELECT correct_answer, points FROM questions WHERE id = %s",
        (question_id,)
    )
    
    if not questions:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    
    question = questions[0]
    is_correct = answer.lower() == question['correct_answer'].lower()
    
    # Calculate points based on speed
    base_points = question['points'] if is_correct else 0
    time_bonus = 0
    
    if is_correct:
        max_time = room['time_per_question']
        if time_taken < max_time * 0.25:
            time_bonus = int(base_points * 0.5)  # 50% bonus for very fast
        elif time_taken < max_time * 0.5:
            time_bonus = int(base_points * 0.25)  # 25% bonus for fast
    
    total_points = base_points + time_bonus
    
    # Update participant score
    participants = execute_query(
        "SELECT id, score, streak FROM game_participants WHERE room_id = %s AND user_id = %s",
        (room['id'], user_id)
    )
    
    if participants:
        participant = participants[0]
        new_streak = participant['streak'] + 1 if is_correct else 0
        streak_bonus = min(new_streak, 5) * 2 if is_correct else 0  # Max 10 streak bonus
        
        new_score = participant['score'] + total_points + streak_bonus
        
        execute_query(
            "UPDATE game_participants SET score = %s, streak = %s WHERE id = %s",
            (new_score, new_streak, participant['id']),
            fetch=False
        )
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': question['correct_answer'],
        'points': total_points,
        'time_bonus': time_bonus,
        'streak_bonus': streak_bonus if participants else 0
    })

@game_bp.route('/leaderboard/<room_code>', methods=['GET'])
def get_leaderboard(room_code):
    """Get current leaderboard for a room"""
    rooms = execute_query(
        "SELECT id FROM game_rooms WHERE room_code = %s",
        (room_code.upper(),)
    )
    
    if not rooms:
        return jsonify({'success': False, 'message': 'Room not found'}), 404
    
    leaderboard = execute_query(
        """SELECT gp.score, gp.streak, u.username, u.avatar, u.rank_badge
           FROM game_participants gp
           JOIN users u ON gp.user_id = u.id
           WHERE gp.room_id = %s
           ORDER BY gp.score DESC""",
        (rooms[0]['id'],)
    ) or []
    
    # Add positions
    for i, player in enumerate(leaderboard):
        player['position'] = i + 1
    
    return jsonify({'success': True, 'leaderboard': leaderboard})

@game_bp.route('/end/<room_code>', methods=['POST'])
def end_game(room_code):
    """End the game and save results"""
    try:
        user_id = session.get('user_id')
        
        rooms = execute_query(
            """SELECT gr.*, q.id as quiz_id,
                      (SELECT COUNT(*) FROM questions WHERE quiz_id = gr.quiz_id) as total_questions
               FROM game_rooms gr
               JOIN quizzes q ON gr.quiz_id = q.id
               WHERE gr.room_code = %s AND gr.host_id = %s""",
            (room_code.upper(), user_id)
        )
        
        if not rooms:
            return jsonify({'success': False, 'message': 'Room not found or you are not the host'}), 403
        
        room = rooms[0]
        
        # Get final results
        participants = execute_query(
            """SELECT gp.user_id, gp.score, u.username, u.avatar
               FROM game_participants gp
               JOIN users u ON gp.user_id = u.id
               WHERE gp.room_id = %s
               ORDER BY gp.score DESC""",
            (room['id'],)
        ) or []
        
        # Save results to quiz_results table
        for participant in participants:
            try:
                execute_query(
                    """INSERT INTO quiz_results (user_id, quiz_id, score, total_questions)
                       VALUES (%s, %s, %s, %s)""",
                    (participant['user_id'], room['quiz_id'], 
                     participant['score'], room['total_questions']),
                    fetch=False
                )
            except Exception as e:
                print(f"Error saving result for user {participant['user_id']}: {e}")
        
        # Update room status
        execute_query(
            "UPDATE game_rooms SET status = 'ended' WHERE id = %s",
            (room['id'],),
            fetch=False
        )
        
        return jsonify({
            'success': True,
            'message': 'Game ended!',
            'final_results': participants
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error ending game: {str(e)}'}), 500

@game_bp.route('/my-rooms', methods=['GET'])
def my_rooms():
    """Get rooms hosted by current user"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    rooms = execute_query(
        """SELECT gr.*, q.title as quiz_title,
                  (SELECT COUNT(*) FROM game_participants WHERE room_id = gr.id) as participant_count
           FROM game_rooms gr
           JOIN quizzes q ON gr.quiz_id = q.id
           WHERE gr.host_id = %s
           ORDER BY gr.created_at DESC
           LIMIT 20""",
        (user_id,)
    ) or []
    
    for room in rooms:
        if room.get('started_at'):
            room['started_at'] = room['started_at'].isoformat()
        if room.get('created_at'):
            room['created_at'] = room['created_at'].isoformat()
    
    return jsonify({'success': True, 'rooms': rooms})
