"""
Quiz Master Pro - Main Application
Flask application with WebSocket support for real-time features
"""
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from config import Config
from database import init_database

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app)

# Initialize SocketIO for real-time features
# Initialize SocketIO for real-time features
# Using threading mode to avoid eventlet/gevent compatibility issues on Python 3.14
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Import routes
from routes.auth import auth_bp
from routes.quiz import quiz_bp
from routes.questions import questions_bp
from routes.game import game_bp
from routes.practice import practice_bp
from routes.battle import battle_bp
from routes.chat import chat_bp
from routes.admin import admin_bp
from routes.exam import exam_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
app.register_blueprint(questions_bp, url_prefix='/api/questions')
app.register_blueprint(game_bp, url_prefix='/api/game')
app.register_blueprint(practice_bp, url_prefix='/api/practice')
app.register_blueprint(battle_bp, url_prefix='/api/battle')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(exam_bp, url_prefix='/api/exam')

# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

# ============================================
# SERVER PORTAL ROUTES (Admin & Teacher)
# ============================================

@app.route('/server')
@app.route('/server/')
def server_index():
    """Server portal home - redirect to login"""
    if 'user_id' in session and session.get('role') in ['admin', 'teacher']:
        return redirect(url_for('server_dashboard'))
    return redirect(url_for('server_login'))

@app.route('/server/login')
def server_login():
    """Server portal login page"""
    return render_template('server/login.html')

@app.route('/server/dashboard')
def server_dashboard():
    """Server portal dashboard"""
    if 'user_id' not in session or session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('server_login'))
    
    if session.get('role') == 'admin':
        return render_template('server/admin/dashboard.html')
    return render_template('server/teacher/dashboard.html')

@app.route('/server/admin/users')
def admin_users():
    """Admin user management"""
    if session.get('role') != 'admin':
        return redirect(url_for('server_login'))
    return render_template('server/admin/users.html')

@app.route('/server/admin/analytics')
def admin_analytics():
    """Admin analytics page"""
    if session.get('role') != 'admin':
        return redirect(url_for('server_login'))
    return render_template('server/admin/analytics.html')

@app.route('/server/admin/categories')
def admin_categories():
    """Admin categories management"""
    if session.get('role') != 'admin':
        return redirect(url_for('server_login'))
    return render_template('server/admin/categories.html')

@app.route('/server/admin/quizzes')
def admin_quizzes():
    """Admin view all quizzes"""
    if session.get('role') != 'admin':
        return redirect(url_for('server_login'))
    return render_template('server/admin/quizzes.html')

@app.route('/server/teacher/create-quiz')
def teacher_create_quiz():
    """Teacher create quiz page"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('server_login'))
    return render_template('server/teacher/create_quiz.html')

@app.route('/server/teacher/question-bank')
def teacher_question_bank():
    """Teacher question bank page"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('server_login'))
    return render_template('server/teacher/question_bank.html')

@app.route('/server/teacher/host-game')
def teacher_host_game():
    """Teacher host game page"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('server_login'))
    return render_template('server/teacher/host_game.html')

@app.route('/server/teacher/results')
def teacher_results():
    """Teacher results page"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('server_login'))
    return render_template('server/teacher/results.html')

@app.route('/server/teacher/exams')
def teacher_exams():
    """Teacher exam management page"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('server_login'))
    return render_template('server/teacher/exams.html')

# ============================================
# CLIENT PORTAL ROUTES (Students)
# ============================================

@app.route('/client')
@app.route('/client/')
def client_index():
    """Client portal home - redirect to login or dashboard"""
    if 'user_id' in session and session.get('role') == 'student':
        return redirect(url_for('client_home'))
    return redirect(url_for('client_login'))

@app.route('/client/login')
def client_login():
    """Client portal login page"""
    return render_template('client/login.html')

@app.route('/client/register')
def client_register():
    """Client portal registration page"""
    return render_template('client/register.html')

@app.route('/client/home')
def client_home():
    """Client home dashboard"""
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('client_login'))
    return render_template('client/home.html')

@app.route('/client/game')
@app.route('/client/game/<room_code>')
def client_game(room_code=None):
    """Client game page"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/game.html', room_code=room_code)

@app.route('/client/practice')
def client_practice():
    """Client practice mode"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/practice.html')

@app.route('/client/battle')
def client_battle():
    """Client battle mode"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/battle.html')

@app.route('/client/chat')
def client_chat():
    """Client chat room"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/chat.html')

@app.route('/client/profile')
def client_profile():
    """Client profile page"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/profile.html')

@app.route('/client/leaderboard')
def client_leaderboard():
    """Client leaderboard page"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/leaderboard.html')

@app.route('/client/exams')
def client_exams():
    """Client exams page"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/exams.html')

@app.route('/client/exam/<int:exam_id>')
def client_exam(exam_id):
    """Client take exam page"""
    if 'user_id' not in session:
        return redirect(url_for('client_login'))
    return render_template('client/exam.html', exam_id=exam_id)

# ============================================
# WEBSOCKET EVENTS
# ============================================

# Store active connections
active_users = {}
game_rooms = {}
chat_rooms = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")

@socketio.on('login')
def handle_login(data):
    """Handle user login for live tracking"""
    user_id = data.get('user_id')
    username = data.get('username')
    
    if user_id:
        active_users[request.sid] = {'user_id': user_id, 'username': username}
        
        # Broadcast active user count
        emit('active_users_update', {
            'count': len(active_users),
            'users': list(active_users.values())
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    sid = request.sid
    if sid in active_users:
        user = active_users[sid]
        del active_users[sid]
        print(f"User {user.get('username')} disconnected")
        
        # Broadcast update
        emit('active_users_update', {
            'count': len(active_users)
        }, broadcast=True)

# Game Events
@socketio.on('join_game')
def handle_join_game(data):
    """Handle joining a game room"""
    room_code = data.get('room_code')
    username = data.get('username')
    user_id = data.get('user_id')
    avatar = data.get('avatar', 'avatar1')
    
    join_room(room_code)
    
    if room_code not in game_rooms:
        game_rooms[room_code] = {'players': []}
    
    # Check if player already joined
    existing_player = next((p for p in game_rooms[room_code]['players'] if p['user_id'] == user_id), None)
    
    if existing_player:
        # Update existing player session
        existing_player['sid'] = request.sid
        existing_player['username'] = username 
        existing_player['avatar'] = avatar
    else:
        # Add new player
        player_info = {
            'user_id': user_id, 
            'username': username, 
            'avatar': avatar,
            'score': 0, 
            'sid': request.sid
        }
        game_rooms[room_code]['players'].append(player_info)
        
    print(f"Player joined room {room_code}: {username} (Total: {len(game_rooms[room_code]['players'])})")
    
    emit('player_joined', {
        'username': username,
        'player_count': len(game_rooms[room_code]['players']),
        'players': game_rooms[room_code]['players']
    }, room=room_code)

@socketio.on('host_game')
def handle_host_game(data):
    """Handle host joining the game room"""
    room_code = data.get('room_code')
    join_room(room_code)
    
    if room_code not in game_rooms:
        game_rooms[room_code] = {'players': []}
        
    print(f"Host joined room: {room_code}")

@socketio.on('leave_game')
def handle_leave_game(data):
    """Handle leaving a game room"""
    room_code = data.get('room_code')
    username = data.get('username')
    
    leave_room(room_code)
    
    if room_code in game_rooms:
        game_rooms[room_code]['players'] = [
            p for p in game_rooms[room_code]['players'] 
            if p['username'] != username
        ]
        
        emit('player_left', {
            'username': username,
            'player_count': len(game_rooms[room_code]['players'])
        }, room=room_code)

@socketio.on('start_game')
def handle_start_game(data):
    """Host starts the game"""
    room_code = data.get('room_code')
    print(f"DEBUG: start_game socket event for room {room_code}")
    emit('game_started', {}, room=room_code)

@socketio.on('new_question')
def handle_new_question(data):
    """Send question to all players (from host)"""
    room_code = data.get('room_code')
    question = data.get('question')
    question_number = data.get('question_number')
    total_questions = data.get('total_questions')
    
    print(f"DEBUG: new_question for room {room_code}, Q{question_number}/{total_questions}")
    
    emit('new_question', {
        'question': question,
        'question_number': question_number,
        'total_questions': total_questions
    }, room=room_code)

@socketio.on('next_question')
def handle_next_question(data):
    """Legacy handler - redirects to new_question"""
    room_code = data.get('room_code')
    question = data.get('question')
    question_number = data.get('question_number')
    total_questions = data.get('total_questions')
    
    emit('new_question', {
        'question': question,
        'question_number': question_number,
        'total_questions': total_questions
    }, room=room_code)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Handle answer submission"""
    room_code = data.get('room_code')
    user_id = data.get('user_id')
    username = data.get('username')
    answer = data.get('answer')
    time_taken = data.get('time_taken')
    is_correct = data.get('is_correct')
    points = data.get('points', 0)
    
    # Update player score
    if room_code in game_rooms:
        for player in game_rooms[room_code]['players']:
            if player['user_id'] == user_id:
                player['score'] += points
                break
        
        # Send to host
        emit('answer_received', {
            'username': username,
            'is_correct': is_correct,
            'points': points
        }, room=room_code)

@socketio.on('show_leaderboard')
def handle_show_leaderboard(data):
    """Show leaderboard to all players"""
    room_code = data.get('room_code')
    
    if room_code in game_rooms:
        players = sorted(game_rooms[room_code]['players'], 
                        key=lambda x: x['score'], reverse=True)
        
        emit('leaderboard_update', {
            'leaderboard': players
        }, room=room_code)

@socketio.on('end_game')
def handle_end_game(data):
    """End the game and show final results"""
    room_code = data.get('room_code')
    
    if room_code in game_rooms:
        players = sorted(game_rooms[room_code]['players'], 
                        key=lambda x: x['score'], reverse=True)
        
        emit('game_ended', {
            'final_leaderboard': players
        }, room=room_code)

# Chat Events
@socketio.on('join_chat')
def handle_join_chat(data):
    """Join a chat room"""
    room_id = f"chat_{data.get('room_id')}"
    username = data.get('username')
    
    join_room(room_id)
    
    emit('user_joined_chat', {
        'username': username,
        'message': f'{username} joined the chat'
    }, room=room_id)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    """Leave a chat room"""
    room_id = f"chat_{data.get('room_id')}"
    username = data.get('username')
    
    leave_room(room_id)
    
    emit('user_left_chat', {
        'username': username,
        'message': f'{username} left the chat'
    }, room=room_id)

@socketio.on('send_message')
def handle_send_message(data):
    """Handle chat message"""
    room_id = f"chat_{data.get('room_id')}"
    
    emit('new_message', {
        'sender_id': data.get('sender_id'),
        'username': data.get('username'),
        'avatar': data.get('avatar'),
        'message': data.get('message'),
        'message_type': data.get('message_type', 'text'),
        'timestamp': data.get('timestamp')
    }, room=room_id)

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    room_id = f"chat_{data.get('room_id')}"
    
    emit('user_typing', {
        'username': data.get('username'),
        'is_typing': data.get('is_typing')
    }, room=room_id, include_self=False)

# Battle Events
@socketio.on('join_battle')
def handle_join_battle(data):
    """Join a battle match"""
    battle_id = f"battle_{data.get('battle_id')}"
    join_room(battle_id)
    
    emit('opponent_joined', {
        'opponent': data.get('username')
    }, room=battle_id, include_self=False)

@socketio.on('battle_answer')
def handle_battle_answer(data):
    """Handle battle answer submission"""
    battle_id = f"battle_{data.get('battle_id')}"
    
    emit('opponent_answered', {
        'user_id': data.get('user_id'),
        'is_correct': data.get('is_correct'),
        'points': data.get('points')
    }, room=battle_id)

@socketio.on('battle_complete')
def handle_battle_complete(data):
    """Handle battle completion"""
    battle_id = f"battle_{data.get('battle_id')}"
    
    emit('battle_ended', {
        'winner': data.get('winner'),
        'player1_score': data.get('player1_score'),
        'player2_score': data.get('player2_score')
    }, room=battle_id)

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("Initializing Quiz Master Pro...")
    init_database()
    print(f"Server starting on http://{Config.HOST}:{Config.PORT}")
    print(f"Client Portal: http://localhost:{Config.PORT}/client")
    print(f"Server Portal: http://localhost:{Config.PORT}/server")
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, allow_unsafe_werkzeug=True)
