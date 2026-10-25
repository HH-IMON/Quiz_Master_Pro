/**
 * Quiz Master Pro - Authentication JavaScript
 * Login and Registration handling
 */

// ============================================
// LOGIN FORM HANDLER
// ============================================

async function handleLogin(event, portal = 'client') {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    const username = form.querySelector('[name="username"]').value.trim();
    const password = form.querySelector('[name="password"]').value;

    if (!username || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    showLoading(submitBtn);

    try {
        const result = await api.post('/auth/login', {
            username,
            password,
            portal
        });

        if (result.success) {
            showToast('Login successful!', 'success');

            // Redirect based on role
            setTimeout(() => {
                if (portal === 'server') {
                    window.location.href = '/server/dashboard';
                } else {
                    window.location.href = '/client/home';
                }
            }, 500);
        }
    } catch (error) {
        showToast(error.message || 'Login failed', 'error');
    } finally {
        hideLoading(submitBtn);
    }
}

// ============================================
// REGISTRATION FORM HANDLER
// ============================================

async function handleRegister(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    const username = form.querySelector('[name="username"]').value.trim();
    const email = form.querySelector('[name="email"]').value.trim();
    const password = form.querySelector('[name="password"]').value;
    const confirmPassword = form.querySelector('[name="confirmPassword"]')?.value;
    const avatar = form.querySelector('[name="avatar"]')?.value || 'avatar1';

    // Validation
    if (!username || !email || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    if (username.length < 3) {
        showToast('Username must be at least 3 characters', 'error');
        return;
    }

    if (password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }

    if (confirmPassword && password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }

    if (!validateEmail(email)) {
        showToast('Please enter a valid email', 'error');
        return;
    }

    showLoading(submitBtn);

    try {
        const result = await api.post('/auth/register', {
            username,
            email,
            password,
            role: 'student',
            avatar
        });

        if (result.success) {
            showToast('Registration successful! Please login.', 'success');

            setTimeout(() => {
                window.location.href = '/client/login';
            }, 1000);
        }
    } catch (error) {
        showToast(error.message || 'Registration failed', 'error');
    } finally {
        hideLoading(submitBtn);
    }
}

// ============================================
// TEACHER/ADMIN REGISTRATION
// ============================================

async function handleTeacherRegister(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    const username = form.querySelector('[name="username"]').value.trim();
    const email = form.querySelector('[name="email"]').value.trim();
    const password = form.querySelector('[name="password"]').value;
    const role = form.querySelector('[name="role"]')?.value || 'teacher';

    if (!username || !email || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    showLoading(submitBtn);

    try {
        const result = await api.post('/auth/register', {
            username,
            email,
            password,
            role
        });

        if (result.success) {
            showToast('Account created successfully!', 'success');
            hideModal('register-modal');
            // Refresh user list if on admin page
            if (typeof loadUsers === 'function') {
                loadUsers();
            }
        }
    } catch (error) {
        showToast(error.message || 'Registration failed', 'error');
    } finally {
        hideLoading(submitBtn);
    }
}

// ============================================
// LOGOUT HANDLER
// ============================================

async function handleLogout() {
    try {
        await api.post('/auth/logout');
        showToast('Logged out successfully', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 500);
    } catch (error) {
        // Redirect anyway
        window.location.href = '/';
    }
}

// ============================================
// AUTO-LOGOUT (Inactivity Timer)
// ============================================

const AUTO_LOGOUT_TIME = 30 * 60 * 1000; // 30 minutes
let inactivityTimer = null;

function resetInactivityTimer() {
    if (inactivityTimer) {
        clearTimeout(inactivityTimer);
    }
    inactivityTimer = setTimeout(() => {
        showToast('Session expired due to inactivity', 'warning');
        setTimeout(() => {
            handleLogout();
        }, 2000);
    }, AUTO_LOGOUT_TIME);
}

function initAutoLogout() {
    // Only on authenticated pages
    if (window.location.pathname.includes('/login') ||
        window.location.pathname.includes('/register') ||
        window.location.pathname === '/') {
        return;
    }

    // Track user activity
    ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, { passive: true });
    });

    resetInactivityTimer();
}

// ============================================
// AVATAR SELECTION
// ============================================

function initAvatarSelection() {
    const avatarGrid = document.querySelector('.avatar-grid');
    const avatarInput = document.querySelector('[name="avatar"]');

    if (!avatarGrid || !avatarInput) return;

    const avatars = [
        { key: 'avatar1', emoji: '😀' },
        { key: 'avatar2', emoji: '😎' },
        { key: 'avatar3', emoji: '🤓' },
        { key: 'avatar4', emoji: '🦊' },
        { key: 'avatar5', emoji: '🐱' },
        { key: 'avatar6', emoji: '🐶' },
        { key: 'avatar7', emoji: '🦁' },
        { key: 'avatar8', emoji: '🐼' },
        { key: 'avatar9', emoji: '🦄' },
        { key: 'avatar10', emoji: '🐲' }
    ];

    avatarGrid.innerHTML = avatars.map(avatar => `
        <div class="avatar-option ${avatar.key === avatarInput.value ? 'selected' : ''}" 
             data-avatar="${avatar.key}">
            <span class="avatar-emoji">${avatar.emoji}</span>
        </div>
    `).join('');

    avatarGrid.addEventListener('click', (e) => {
        const option = e.target.closest('.avatar-option');
        if (!option) return;

        // Remove previous selection
        avatarGrid.querySelectorAll('.avatar-option').forEach(el => {
            el.classList.remove('selected');
        });

        // Select new avatar
        option.classList.add('selected');
        avatarInput.value = option.dataset.avatar;
    });
}

// ============================================
// PASSWORD VISIBILITY TOGGLE
// ============================================

function togglePasswordVisibility(button) {
    const input = button.previousElementSibling;
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = '🙈';
    } else {
        input.type = 'password';
        button.textContent = '👁️';
    }
}

// ============================================
// EMAIL VALIDATION
// ============================================

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize avatar selection if on registration page
    initAvatarSelection();

    // Add form event listeners
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        const portal = loginForm.dataset.portal || 'client';
        loginForm.addEventListener('submit', (e) => handleLogin(e, portal));
    }

    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Logout buttons
    document.querySelectorAll('.logout-btn').forEach(btn => {
        btn.addEventListener('click', handleLogout);
    });

    // Initialize auto-logout timer
    initAutoLogout();
});
