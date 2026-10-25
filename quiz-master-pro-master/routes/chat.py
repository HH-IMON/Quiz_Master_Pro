"""
Quiz Master Pro - Chat Routes
Real-time chat functionality for student Q&A
"""
from flask import Blueprint, request, jsonify, session
from database import execute_query
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/rooms', methods=['GET'])
def get_chat_rooms():
    """Get available chat rooms"""
    user_id = session.get('user_id')
    
    rooms = execute_query("""
        SELECT cr.*, 
               u.username as created_by_name,
               q.title as quiz_title,
               (SELECT COUNT(*) FROM chat_messages WHERE room_id = cr.id) as message_count
        FROM chat_rooms cr
        LEFT JOIN users u ON cr.created_by = u.id
        LEFT JOIN quizzes q ON cr.quiz_id = q.id
        WHERE cr.type = 'public' OR cr.created_by = %s
        ORDER BY cr.created_at DESC
    """, (user_id,)) or []
    
    for room in rooms:
        if room.get('created_at'):
            room['created_at'] = room['created_at'].isoformat()
    
    return jsonify({'success': True, 'rooms': rooms})

@chat_bp.route('/room/<int:room_id>', methods=['GET'])
def get_room_details(room_id):
    """Get chat room details"""
    rooms = execute_query(
        """SELECT cr.*, u.username as created_by_name
           FROM chat_rooms cr
           LEFT JOIN users u ON cr.created_by = u.id
           WHERE cr.id = %s""",
        (room_id,)
    )
    
    if not rooms:
        return jsonify({'success': False, 'message': 'Room not found'}), 404
    
    room = rooms[0]
    if room.get('created_at'):
        room['created_at'] = room['created_at'].isoformat()
    
    return jsonify({'success': True, 'room': room})

@chat_bp.route('/create-room', methods=['POST'])
def create_room():
    """Create a new chat room"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    name = data.get('name', '').strip()
    room_type = data.get('type', 'public')
    quiz_id = data.get('quiz_id')
    
    if not name:
        return jsonify({'success': False, 'message': 'Room name is required'}), 400
    
    room_id = execute_query(
        """INSERT INTO chat_rooms (name, type, quiz_id, created_by)
           VALUES (%s, %s, %s, %s)""",
        (name, room_type, quiz_id, user_id),
        fetch=False
    )
    
    if room_id:
        return jsonify({
            'success': True,
            'message': 'Chat room created!',
            'room_id': room_id
        })
    
    return jsonify({'success': False, 'message': 'Failed to create room'}), 500

@chat_bp.route('/messages/<int:room_id>', methods=['GET'])
def get_messages(room_id):
    """Get messages for a chat room"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    messages = execute_query(
        """SELECT cm.*, u.username, u.avatar, u.rank_badge,
                  pm.message as parent_message_text,
                  pu.username as parent_username
           FROM chat_messages cm
           JOIN users u ON cm.sender_id = u.id
           LEFT JOIN chat_messages pm ON cm.parent_message_id = pm.id
           LEFT JOIN users pu ON pm.sender_id = pu.id
           WHERE cm.room_id = %s
           ORDER BY cm.sent_at DESC
           LIMIT %s OFFSET %s""",
        (room_id, limit, offset)
    ) or []
    
    # Reverse to show oldest first
    messages = list(reversed(messages))
    
    for msg in messages:
        if msg.get('sent_at'):
            msg['sent_at'] = msg['sent_at'].isoformat()
    
    return jsonify({'success': True, 'messages': messages})

@chat_bp.route('/send', methods=['POST'])
def send_message():
    """Send a chat message"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    room_id = data.get('room_id')
    message = data.get('message', '').strip()
    message_type = data.get('message_type', 'text')
    parent_message_id = data.get('parent_message_id')
    
    if not room_id or not message:
        return jsonify({'success': False, 'message': 'Room ID and message are required'}), 400
    
    message_id = execute_query(
        """INSERT INTO chat_messages (room_id, sender_id, message, message_type, parent_message_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (room_id, user_id, message, message_type, parent_message_id),
        fetch=False
    )
    
    if message_id:
        # Get the created message with user info
        messages = execute_query(
            """SELECT cm.*, u.username, u.avatar, u.rank_badge
               FROM chat_messages cm
               JOIN users u ON cm.sender_id = u.id
               WHERE cm.id = %s""",
            (message_id,)
        )
        
        if messages:
            msg = messages[0]
            if msg.get('sent_at'):
                msg['sent_at'] = msg['sent_at'].isoformat()
            
            return jsonify({
                'success': True,
                'message': msg
            })
    
    return jsonify({'success': False, 'message': 'Failed to send message'}), 500

@chat_bp.route('/delete-message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a chat message (owner only)"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    # Check ownership
    messages = execute_query(
        "SELECT sender_id FROM chat_messages WHERE id = %s",
        (message_id,)
    )
    
    if not messages:
        return jsonify({'success': False, 'message': 'Message not found'}), 404
    
    if messages[0]['sender_id'] != user_id and session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'You can only delete your own messages'}), 403
    
    execute_query("DELETE FROM chat_messages WHERE id = %s", (message_id,), fetch=False)
    
    return jsonify({'success': True, 'message': 'Message deleted'})

@chat_bp.route('/quiz-room/<int:quiz_id>', methods=['GET'])
def get_quiz_chat_room(quiz_id):
    """Get or create chat room for a quiz"""
    # Check if room exists
    rooms = execute_query(
        "SELECT * FROM chat_rooms WHERE quiz_id = %s AND type = 'quiz_discussion'",
        (quiz_id,)
    )
    
    if rooms:
        room = rooms[0]
        if room.get('created_at'):
            room['created_at'] = room['created_at'].isoformat()
        return jsonify({'success': True, 'room': room})
    
    # Get quiz title
    quizzes = execute_query(
        "SELECT title, created_by FROM quizzes WHERE id = %s",
        (quiz_id,)
    )
    
    if not quizzes:
        return jsonify({'success': False, 'message': 'Quiz not found'}), 404
    
    quiz = quizzes[0]
    
    # Create room
    room_id = execute_query(
        """INSERT INTO chat_rooms (name, type, quiz_id, created_by)
           VALUES (%s, 'quiz_discussion', %s, %s)""",
        (f"Discussion: {quiz['title']}", quiz_id, quiz['created_by']),
        fetch=False
    )
    
    if room_id:
        rooms = execute_query(
            "SELECT * FROM chat_rooms WHERE id = %s",
            (room_id,)
        )
        
        if rooms:
            room = rooms[0]
            if room.get('created_at'):
                room['created_at'] = room['created_at'].isoformat()
            return jsonify({'success': True, 'room': room})
    
    return jsonify({'success': False, 'message': 'Failed to create room'}), 500

@chat_bp.route('/online-users/<int:room_id>', methods=['GET'])
def get_online_users(room_id):
    """Get users currently online in a room"""
    # This would typically use WebSocket tracking
    # For now, return recent active users
    users = execute_query(
        """SELECT DISTINCT u.id, u.username, u.avatar, u.rank_badge
           FROM chat_messages cm
           JOIN users u ON cm.sender_id = u.id
           WHERE cm.room_id = %s 
           AND cm.sent_at > DATE_SUB(NOW(), INTERVAL 30 MINUTE)
           ORDER BY cm.sent_at DESC
           LIMIT 20""",
        (room_id,)
    ) or []
    
    return jsonify({'success': True, 'users': users})
