"""
Quiz Master Pro - Battle Routes
1v1 and team battle mode functionality
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
import json
import random

battle_bp = Blueprint('battle', __name__)

@battle_bp.route('/create', methods=['POST'])
def create_battle():
    """Create a new battle"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    battle_type = data.get('battle_type', '1v1')
    category_id = data.get('category_id')
    opponent_id = data.get('opponent_id')  # For private challenges
    
    # Get a random quiz from the category
    query = """
        SELECT q.id 
        FROM quizzes q 
        WHERE q.is_active = TRUE
    """
    params = []
    
    if category_id:
        query += " AND q.category_id = %s"
        params.append(category_id)
    
    query += " ORDER BY RAND() LIMIT 1"
    
    quizzes = execute_query(query, tuple(params) if params else None)
    
    if not quizzes:
        return jsonify({'success': False, 'message': 'No quizzes available for battle'}), 400
    
    quiz_id = quizzes[0]['id']
    
    # Select random questions and store them for both players
    questions = execute_query(
        "SELECT id FROM questions WHERE quiz_id = %s ORDER BY RAND() LIMIT 10",
        (quiz_id,)
    ) or []
    
    question_ids = json.dumps([q['id'] for q in questions])
    
    battle_id = execute_query(
        """INSERT INTO battle_matches (battle_type, quiz_id, question_ids, player1_id, player2_id, status)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (battle_type, quiz_id, question_ids, user_id, opponent_id, 'waiting'),
        fetch=False
    )
    
    if battle_id:
        return jsonify({
            'success': True,
            'message': 'Battle created!',
            'battle_id': battle_id,
            'quiz_id': quiz_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to create battle'}), 500

@battle_bp.route('/find-opponent', methods=['POST'])
def find_opponent():
    """Find an opponent for matchmaking"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    category_id = data.get('category_id')
    
    # Look for waiting battles
    query = """
        SELECT bm.*, q.title as quiz_title, u.username as player1_name
        FROM battle_matches bm
        JOIN quizzes q ON bm.quiz_id = q.id
        JOIN users u ON bm.player1_id = u.id
        WHERE bm.status = 'waiting' 
        AND bm.player1_id != %s
        AND bm.player2_id IS NULL
    """
    params = [user_id]
    
    if category_id:
        query += " AND q.category_id = %s"
        params.append(category_id)
    
    query += " ORDER BY bm.match_time ASC LIMIT 1"
    
    battles = execute_query(query, tuple(params))
    
    if battles:
        battle = battles[0]
        
        # Join the battle
        execute_query(
            "UPDATE battle_matches SET player2_id = %s, status = 'active' WHERE id = %s",
            (user_id, battle['id']),
            fetch=False
        )
        
        return jsonify({
            'success': True,
            'found': True,
            'battle_id': battle['id'],
            'quiz_id': battle['quiz_id'],
            'opponent': battle['player1_name']
        })
    
    # No opponent found, create a new waiting battle
    return jsonify({
        'success': True,
        'found': False,
        'message': 'Waiting for opponent...'
    })

@battle_bp.route('/get/<int:battle_id>', methods=['GET'])
def get_battle(battle_id):
    """Get battle details"""
    battles = execute_query(
        """SELECT bm.*, 
                  q.title as quiz_title, q.time_per_question,
                  u1.username as player1_name, u1.avatar as player1_avatar,
                  u2.username as player2_name, u2.avatar as player2_avatar
           FROM battle_matches bm
           JOIN quizzes q ON bm.quiz_id = q.id
           JOIN users u1 ON bm.player1_id = u1.id
           LEFT JOIN users u2 ON bm.player2_id = u2.id
           WHERE bm.id = %s""",
        (battle_id,)
    )
    
    if not battles:
        return jsonify({'success': False, 'message': 'Battle not found'}), 404
    
    battle = battles[0]
    if battle.get('match_time'):
        battle['match_time'] = battle['match_time'].isoformat()
    
    return jsonify({'success': True, 'battle': battle})

@battle_bp.route('/questions/<int:battle_id>', methods=['GET'])
def get_battle_questions(battle_id):
    """Get questions for a battle - returns same questions for both players"""
    battles = execute_query(
        "SELECT quiz_id, question_ids FROM battle_matches WHERE id = %s",
        (battle_id,)
    )
    
    if not battles:
        return jsonify({'success': False, 'message': 'Battle not found'}), 404
    
    battle = battles[0]
    
    # Use stored question_ids if available, otherwise fallback to random
    question_ids = battle.get('question_ids')
    if question_ids:
        # Parse stored question IDs
        if isinstance(question_ids, str):
            question_ids = json.loads(question_ids)
        
        # Fetch questions in the stored order
        placeholders = ','.join(['%s'] * len(question_ids))
        questions = execute_query(
            f"""SELECT id, type, question_text, options, points 
               FROM questions WHERE id IN ({placeholders})
               ORDER BY FIELD(id, {placeholders})""",
            tuple(question_ids + question_ids)
        ) or []
    else:
        # Fallback for old battles without stored questions
        questions = execute_query(
            """SELECT id, type, question_text, options, points 
               FROM questions WHERE quiz_id = %s ORDER BY id LIMIT 10""",
            (battle['quiz_id'],)
        ) or []
    
    for q in questions:
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            except:
                pass
    
    return jsonify({'success': True, 'questions': questions})

@battle_bp.route('/submit-answer', methods=['POST'])
def submit_battle_answer():
    """Submit an answer in battle mode"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    battle_id = data.get('battle_id')
    question_id = data.get('question_id')
    answer = data.get('answer', '').strip()
    time_taken = data.get('time_taken', 0)
    
    # Check answer
    questions = execute_query(
        "SELECT correct_answer, points FROM questions WHERE id = %s",
        (question_id,)
    )
    
    if not questions:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    
    question = questions[0]
    is_correct = answer.lower() == question['correct_answer'].lower()
    
    # Calculate points
    base_points = question['points'] if is_correct else 0
    speed_bonus = int(base_points * 0.3) if is_correct and time_taken < 5 else 0
    total_points = base_points + speed_bonus
    
    # Update battle score
    battles = execute_query(
        "SELECT player1_id, player2_id FROM battle_matches WHERE id = %s",
        (battle_id,)
    )
    
    if battles:
        battle = battles[0]
        if user_id == battle['player1_id']:
            execute_query(
                "UPDATE battle_matches SET player1_score = player1_score + %s WHERE id = %s",
                (total_points, battle_id),
                fetch=False
            )
        elif user_id == battle['player2_id']:
            execute_query(
                "UPDATE battle_matches SET player2_score = player2_score + %s WHERE id = %s",
                (total_points, battle_id),
                fetch=False
            )
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'points': total_points,
        'speed_bonus': speed_bonus
    })

@battle_bp.route('/complete', methods=['POST'])
def complete_battle():
    """Complete a battle and determine winner"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    battle_id = data.get('battle_id')
    
    battles = execute_query(
        """SELECT * FROM battle_matches WHERE id = %s""",
        (battle_id,)
    )
    
    if not battles:
        return jsonify({'success': False, 'message': 'Battle not found'}), 404
    
    battle = battles[0]
    
    # Determine winner
    winner_id = None
    if battle['player1_score'] > battle['player2_score']:
        winner_id = battle['player1_id']
    elif battle['player2_score'] > battle['player1_score']:
        winner_id = battle['player2_id']
    # If tie, no winner
    
    execute_query(
        "UPDATE battle_matches SET status = 'completed', winner_id = %s WHERE id = %s",
        (winner_id, battle_id),
        fetch=False
    )
    
    # Award XP to winner
    if winner_id:
        execute_query(
            "UPDATE users SET xp_points = xp_points + 50 WHERE id = %s",
            (winner_id,),
            fetch=False
        )
    
    return jsonify({
        'success': True,
        'winner_id': winner_id,
        'player1_score': battle['player1_score'],
        'player2_score': battle['player2_score']
    })

@battle_bp.route('/history', methods=['GET'])
def get_battle_history():
    """Get user's battle history"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    battles = execute_query(
        """SELECT bm.*, 
                  q.title as quiz_title,
                  u1.username as player1_name,
                  u2.username as player2_name
           FROM battle_matches bm
           JOIN quizzes q ON bm.quiz_id = q.id
           JOIN users u1 ON bm.player1_id = u1.id
           LEFT JOIN users u2 ON bm.player2_id = u2.id
           WHERE (bm.player1_id = %s OR bm.player2_id = %s)
           AND bm.status = 'completed'
           ORDER BY bm.match_time DESC
           LIMIT 20""",
        (user_id, user_id)
    ) or []
    
    for battle in battles:
        if battle.get('match_time'):
            battle['match_time'] = battle['match_time'].isoformat()
        battle['is_winner'] = battle['winner_id'] == user_id
    
    return jsonify({'success': True, 'battles': battles})

@battle_bp.route('/stats', methods=['GET'])
def get_battle_stats():
    """Get user's battle statistics"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    stats = execute_query(
        """SELECT 
              COUNT(*) as total_battles,
              SUM(CASE WHEN winner_id = %s THEN 1 ELSE 0 END) as wins,
              SUM(CASE WHEN winner_id IS NOT NULL AND winner_id != %s 
                  AND (player1_id = %s OR player2_id = %s) THEN 1 ELSE 0 END) as losses,
              SUM(CASE WHEN winner_id IS NULL AND status = 'completed' THEN 1 ELSE 0 END) as ties
           FROM battle_matches
           WHERE (player1_id = %s OR player2_id = %s) AND status = 'completed'""",
        (user_id, user_id, user_id, user_id, user_id, user_id)
    )
    
    if stats:
        stat = stats[0]
        win_rate = round((stat['wins'] / stat['total_battles']) * 100, 1) if stat['total_battles'] > 0 else 0
        stat['win_rate'] = win_rate
        return jsonify({'success': True, 'stats': stat})
    
    return jsonify({'success': True, 'stats': {
        'total_battles': 0, 'wins': 0, 'losses': 0, 'ties': 0, 'win_rate': 0
    }})
