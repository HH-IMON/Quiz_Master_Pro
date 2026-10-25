/**
 * Quiz Master Pro - Main Application JavaScript
 * Common utilities and API functions
 */

// API Base URL
const API_BASE = '/api';

// Current user data
let currentUser = null;

// ============================================
// API UTILITIES
// ============================================

async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Request failed');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Shorthand API methods
const api = {
    get: (endpoint) => apiRequest(endpoint, 'GET'),
    post: (endpoint, data) => apiRequest(endpoint, 'POST', data),
    put: (endpoint, data) => apiRequest(endpoint, 'PUT', data),
    delete: (endpoint) => apiRequest(endpoint, 'DELETE')
};

// ============================================
// AUTHENTICATION
// ============================================

async function getCurrentUser() {
    try {
        const result = await api.get('/auth/me');
        if (result.success) {
            currentUser = result.user;
            return currentUser;
        }
    } catch (error) {
        currentUser = null;
    }
    return null;
}

async function logout() {
    try {
        await api.post('/auth/logout');
    } catch (error) {
        console.error('Logout error:', error);
    }
    window.location.href = '/';
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    return icons[type] || icons.info;
}

// ============================================
// MODAL UTILITIES
// ============================================

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function hideAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.remove('active');
    });
    document.body.style.overflow = '';
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        hideAllModals();
    }
});

// ============================================
// LOADING STATES
// ============================================

function showLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = '<span class="animate-spin">⟳</span> Loading...';
    }
}

function hideLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
        if (element.dataset.originalText) {
            element.innerHTML = element.dataset.originalText;
        }
    }
}

// ============================================
// FORM UTILITIES
// ============================================

function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};

    const formData = new FormData(form);
    const data = {};

    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }

    return data;
}

function clearForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
    }
}

function setFormErrors(errors) {
    // Clear existing errors
    document.querySelectorAll('.form-error').forEach(el => el.remove());
    document.querySelectorAll('.form-input.error').forEach(el => el.classList.remove('error'));

    // Set new errors
    for (const [field, message] of Object.entries(errors)) {
        const input = document.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('error');
            const error = document.createElement('span');
            error.className = 'form-error';
            error.textContent = message;
            input.parentNode.appendChild(error);
        }
    }
}

// ============================================
// DATE & TIME UTILITIES
// ============================================

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateTime(dateString) {
    return `${formatDate(dateString)} ${formatTime(dateString)}`;
}

function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }

    return 'Just now';
}

// ============================================
// STRING UTILITIES
// ============================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(str, length = 50) {
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ============================================
// AVATAR HELPERS
// ============================================

const AVATARS = {
    avatar1: '😀',
    avatar2: '😎',
    avatar3: '🤓',
    avatar4: '🦊',
    avatar5: '🐱',
    avatar6: '🐶',
    avatar7: '🦁',
    avatar8: '🐼',
    avatar9: '🦄',
    avatar10: '🐲'
};

function getAvatarEmoji(avatarKey) {
    return AVATARS[avatarKey] || '😀';
}

function createAvatarElement(avatar, size = '') {
    const sizeClass = size ? `avatar-${size}` : '';
    return `<div class="avatar ${sizeClass}">${getAvatarEmoji(avatar)}</div>`;
}

// ============================================
// LEVEL & XP HELPERS
// ============================================

const LEVELS = {
    1: { name: 'Beginner', xp_required: 0, badge: '🌱' },
    2: { name: 'Learner', xp_required: 100, badge: '📚' },
    3: { name: 'Scholar', xp_required: 300, badge: '🎓' },
    4: { name: 'Expert', xp_required: 600, badge: '⭐' },
    5: { name: 'Master', xp_required: 1000, badge: '👑' },
    6: { name: 'Grandmaster', xp_required: 1500, badge: '🏆' },
    7: { name: 'Legend', xp_required: 2500, badge: '💎' }
};

function getLevelInfo(xp) {
    let level = 1;
    for (const [lvl, info] of Object.entries(LEVELS).reverse()) {
        if (xp >= info.xp_required) {
            level = parseInt(lvl);
            break;
        }
    }
    return { level, ...LEVELS[level] };
}

function getXPProgress(xp) {
    const currentLevel = getLevelInfo(xp);
    const nextLevel = LEVELS[currentLevel.level + 1];

    if (!nextLevel) {
        return { progress: 100, current: xp, required: xp };
    }

    const currentLevelXP = currentLevel.xp_required;
    const xpInLevel = xp - currentLevelXP;
    const xpForNext = nextLevel.xp_required - currentLevelXP;
    const progress = Math.min(100, Math.floor((xpInLevel / xpForNext) * 100));

    return { progress, current: xpInLevel, required: xpForNext };
}

// ============================================
// SOUND EFFECTS
// ============================================

const sounds = {
    correct: null,
    incorrect: null,
    tick: null,
    complete: null
};

function initSounds() {
    // Create audio elements (would need actual sound files)
    // sounds.correct = new Audio('/static/sounds/correct.mp3');
    // sounds.incorrect = new Audio('/static/sounds/incorrect.mp3');
    // sounds.tick = new Audio('/static/sounds/tick.mp3');
    // sounds.complete = new Audio('/static/sounds/complete.mp3');
}

function playSound(name) {
    if (sounds[name]) {
        sounds[name].currentTime = 0;
        sounds[name].play().catch(() => { });
    }
}

// ============================================
// CONFETTI EFFECT
// ============================================

function showConfetti() {
    const container = document.createElement('div');
    container.className = 'confetti-container';
    document.body.appendChild(container);

    const colors = ['#667eea', '#f093fb', '#00d4aa', '#feca57', '#4facfe', '#ff6b6b'];

    for (let i = 0; i < 100; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = `${Math.random() * 100}%`;
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = `${Math.random() * 2}s`;
        confetti.style.animationDuration = `${2 + Math.random() * 2}s`;
        container.appendChild(confetti);
    }

    setTimeout(() => container.remove(), 5000);
}

// ============================================
// PARTICLES BACKGROUND
// ============================================

function initParticles() {
    const container = document.querySelector('.particles');
    if (!container) return;

    // Clear existing particles
    container.innerHTML = '';

    // Create particles
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.animationDelay = `${Math.random() * 15}s`;
        particle.style.animationDuration = `${15 + Math.random() * 10}s`;
        particle.style.width = `${5 + Math.random() * 10}px`;
        particle.style.height = particle.style.width;
        container.appendChild(particle);
    }
}

// ============================================
// SIDEBAR TOGGLE (MOBILE)
// ============================================

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize particles if container exists
    initParticles();

    // Initialize sounds
    initSounds();

    // Get current user and init socket
    getCurrentUser().then(user => {
        if (typeof io !== 'undefined') {
            const socket = io();

            if (user) {
                socket.emit('login', {
                    user_id: user.id,
                    username: user.username
                });
            }

            socket.on('active_users_update', (data) => {
                const badges = document.querySelectorAll('.live-users-badge');
                badges.forEach(badge => {
                    badge.innerHTML = `🔴 ${data.count} Online`;
                    badge.classList.remove('hidden');
                });
            });

            // Make socket available globally
            window.socket = socket;
        }
    });
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, showToast, showModal, hideModal, showConfetti };
}
