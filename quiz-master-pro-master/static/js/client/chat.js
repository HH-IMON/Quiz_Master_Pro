/**
 * Quiz Master Pro - Chat JavaScript
 * Real-time chat with WebSocket
 */

let socket = null;
let currentRoom = null;

// ============================================
// SOCKET INITIALIZATION
// ============================================

function initChatSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Chat connected');
        if (currentRoom) {
            joinChatRoom(currentRoom.id);
        }
    });

    socket.on('disconnect', () => {
        console.log('Chat disconnected');
    });

    // Chat events
    socket.on('new_message', handleNewMessage);
    socket.on('user_joined_chat', handleUserJoinedChat);
    socket.on('user_left_chat', handleUserLeftChat);
    socket.on('user_typing', handleUserTyping);
}

// ============================================
// LOAD CHAT ROOMS
// ============================================

async function loadChatRooms() {
    try {
        const result = await api.get('/chat/rooms');
        renderChatRooms(result.rooms);
    } catch (error) {
        console.error('Failed to load chat rooms:', error);
    }
}

function renderChatRooms(rooms) {
    const container = document.getElementById('room-list');
    if (!container) return;

    container.innerHTML = rooms.map(room => `
        <div class="room-item ${currentRoom?.id === room.id ? 'active' : ''}" 
             data-room-id="${room.id}" onclick="selectRoom(${room.id})">
            <div class="room-icon">
                ${room.type === 'public' ? '💬' : room.type === 'quiz_discussion' ? '📚' : '🔒'}
            </div>
            <div class="room-info">
                <div class="room-name">${escapeHtml(room.name)}</div>
                <div class="room-preview">${room.message_count} messages</div>
            </div>
        </div>
    `).join('');
}

// ============================================
// SELECT & JOIN ROOM
// ============================================

async function selectRoom(roomId) {
    // Leave current room
    if (currentRoom && socket) {
        socket.emit('leave_chat', {
            room_id: currentRoom.id,
            username: currentUser?.username
        });
    }

    try {
        const result = await api.get(`/chat/room/${roomId}`);
        currentRoom = result.room;

        // Update UI
        document.querySelectorAll('.room-item').forEach(item => {
            item.classList.remove('active');
            if (parseInt(item.dataset.roomId) === roomId) {
                item.classList.add('active');
            }
        });

        // Update header
        const chatTitle = document.querySelector('.chat-title h3');
        if (chatTitle) {
            chatTitle.textContent = currentRoom.name;
        }

        // Load messages
        await loadMessages(roomId);

        // Join socket room
        joinChatRoom(roomId);

    } catch (error) {
        showToast('Failed to load room', 'error');
    }
}

function joinChatRoom(roomId) {
    if (socket && currentUser) {
        socket.emit('join_chat', {
            room_id: roomId,
            username: currentUser.username
        });
    }
}

// ============================================
// LOAD & RENDER MESSAGES
// ============================================

async function loadMessages(roomId, offset = 0) {
    try {
        const result = await api.get(`/chat/messages/${roomId}?limit=50&offset=${offset}`);
        renderMessages(result.messages);
        scrollToBottom();
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    container.innerHTML = messages.map(msg => renderMessage(msg)).join('');
}

function renderMessage(msg) {
    const isOwn = msg.sender_id === currentUser?.id;

    let typeIndicator = '';
    if (msg.message_type === 'question') {
        typeIndicator = '<div class="message-type-indicator question">❓ Question</div>';
    } else if (msg.message_type === 'answer') {
        typeIndicator = '<div class="message-type-indicator answer">💡 Answer</div>';
    }

    let replyHtml = '';
    if (msg.parent_message_id && msg.parent_message_text) {
        replyHtml = `
            <div class="message-reply">
                <span class="reply-sender">${escapeHtml(msg.parent_username || 'User')}</span>
                ${escapeHtml(truncate(msg.parent_message_text, 50))}
            </div>
        `;
    }

    return `
        <div class="message ${isOwn ? 'own' : ''}" data-message-id="${msg.id}">
            <div class="message-avatar">
                <div class="avatar avatar-sm">${getAvatarEmoji(msg.avatar)}</div>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${escapeHtml(msg.username)}</span>
                    <span class="message-badge">${msg.rank_badge || ''}</span>
                    <span class="message-time">${timeAgo(msg.sent_at)}</span>
                </div>
                ${replyHtml}
                ${typeIndicator}
                <div class="message-bubble ${msg.message_type}">${escapeHtml(msg.message)}</div>
            </div>
        </div>
    `;
}

function appendMessage(msg) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    // Remove typing indicator
    const typingEl = document.getElementById('typing-indicator');
    if (typingEl) typingEl.remove();

    container.insertAdjacentHTML('beforeend', renderMessage(msg));
    scrollToBottom();
}

function scrollToBottom() {
    const container = document.getElementById('messages-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// ============================================
// SEND MESSAGE
// ============================================

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input?.value?.trim();

    if (!message || !currentRoom) return;

    // Get message type
    const activeType = document.querySelector('.type-btn.active');
    const messageType = activeType?.dataset.type || 'text';

    // Clear input immediately
    input.value = '';

    // Create message object for immediate display
    const newMsg = {
        id: Date.now(),
        sender_id: currentUser.id,
        username: currentUser.username,
        avatar: currentUser.avatar,
        message: message,
        message_type: messageType,
        rank_badge: currentUser.rank_badge || '',
        sent_at: new Date().toISOString()
    };

    // Append own message immediately
    appendMessage(newMsg);

    try {
        const result = await api.post('/chat/send', {
            room_id: currentRoom.id,
            message: message,
            message_type: messageType
        });

        if (result.success) {
            // Emit to socket for other users
            socket.emit('send_message', {
                room_id: currentRoom.id,
                sender_id: currentUser.id,
                username: currentUser.username,
                avatar: currentUser.avatar,
                rank_badge: currentUser.rank_badge || '',
                message: message,
                message_type: messageType,
                timestamp: new Date().toISOString()
            });
        }
    } catch (error) {
        showToast('Failed to send message', 'error');
    }
}

// ============================================
// SOCKET EVENT HANDLERS
// ============================================

function handleNewMessage(data) {
    // Don't duplicate own messages (already shown instantly)
    if (data.sender_id === currentUser?.id) return;

    appendMessage({
        id: Date.now(),
        sender_id: data.sender_id,
        username: data.username || 'Unknown',
        avatar: data.avatar,
        message: data.message,
        message_type: data.message_type,
        rank_badge: data.rank_badge || '',
        sent_at: data.timestamp || new Date().toISOString()
    });
}

function handleUserJoinedChat(data) {
    appendSystemMessage(`${data.username} joined the chat`);
    updateOnlineUsers();
}

function handleUserLeftChat(data) {
    appendSystemMessage(`${data.username} left the chat`);
    updateOnlineUsers();
}

function handleUserTyping(data) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    let typingEl = document.getElementById('typing-indicator');

    if (data.is_typing) {
        if (!typingEl) {
            typingEl = document.createElement('div');
            typingEl.id = 'typing-indicator';
            typingEl.className = 'typing-indicator';
            typingEl.innerHTML = `
                <span>${escapeHtml(data.username)} is typing</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            `;
            container.appendChild(typingEl);
            scrollToBottom();
        }
    } else {
        if (typingEl) typingEl.remove();
    }
}

function appendSystemMessage(text) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    container.insertAdjacentHTML('beforeend', `
        <div class="system-message">
            <span>${escapeHtml(text)}</span>
        </div>
    `);
    scrollToBottom();
}

// ============================================
// TYPING INDICATOR
// ============================================

let typingTimeout = null;

function handleTyping() {
    if (!socket || !currentRoom) return;

    socket.emit('typing', {
        room_id: currentRoom.id,
        username: currentUser?.username,
        is_typing: true
    });

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.emit('typing', {
            room_id: currentRoom.id,
            username: currentUser?.username,
            is_typing: false
        });
    }, 2000);
}

// ============================================
// ONLINE USERS
// ============================================

async function updateOnlineUsers() {
    if (!currentRoom) return;

    try {
        const result = await api.get(`/chat/online-users/${currentRoom.id}`);
        renderOnlineUsers(result.users);
    } catch (error) {
        console.error('Failed to load online users:', error);
    }
}

function renderOnlineUsers(users) {
    const container = document.getElementById('online-users-list');
    if (!container) return;

    container.innerHTML = users.map(user => `
        <div class="online-user">
            <div class="avatar avatar-sm" style="position: relative;">
                ${getAvatarEmoji(user.avatar)}
                <span class="online-status"></span>
            </div>
            <div class="online-user-info">
                <div class="online-user-name">${escapeHtml(user.username)}</div>
            </div>
            <span class="online-user-badge">${user.rank_badge || ''}</span>
        </div>
    `).join('');

    // Update count
    const countEl = document.querySelector('.online-count span');
    if (countEl) {
        countEl.textContent = `${users.length} online`;
    }
}

// ============================================
// MESSAGE TYPE TOGGLE
// ============================================

function setMessageType(type) {
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        }
    });
}

// ============================================
// CREATE ROOM
// ============================================

async function createChatRoom(name, type = 'public') {
    try {
        const result = await api.post('/chat/create-room', { name, type });
        if (result.success) {
            showToast('Room created!', 'success');
            loadChatRooms();
            hideModal('create-room-modal');
        }
    } catch (error) {
        showToast(error.message || 'Failed to create room', 'error');
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    // Get current user
    await getCurrentUser();

    // Initialize socket
    initChatSocket();

    // Load rooms
    await loadChatRooms();

    // Select first room if available
    const firstRoom = document.querySelector('.room-item');
    if (firstRoom) {
        selectRoom(parseInt(firstRoom.dataset.roomId));
    }

    // Chat input events
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            } else {
                handleTyping();
            }
        });
    }

    // Send button
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    // Message type buttons
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.addEventListener('click', () => setMessageType(btn.dataset.type));
    });
});
