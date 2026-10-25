/**
 * Quiz Master Pro - Game JavaScript
 * Real-time game interface for students
 */

// Socket connection
let socket = null;
let gameState = {
    roomCode: null,
    questions: [],
    currentQuestion: 0,
    score: 0,
    streak: 0,
    isHost: false,
    timeLeft: 30,
    hasAnswered: false
};

let timerInterval = null;
let participantRefreshInterval = null;

// ============================================
// SOCKET INITIALIZATION
// ============================================

function initSocket() {
    if (window.socket && window.socket.connected) {
        socket = window.socket;
    } else {
        socket = io();
    }

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showToast('Connection lost. Reconnecting...', 'warning');
    });

    // Game events
    socket.on('player_joined', handlePlayerJoined);
    socket.on('player_left', handlePlayerLeft);
    socket.on('game_started', handleGameStarted);
    socket.on('new_question', handleNewQuestion);
    socket.on('leaderboard_update', handleLeaderboardUpdate);
    socket.on('game_ended', handleGameEnded);
    socket.on('answer_received', handleAnswerReceived);
}

// ============================================
// JOIN GAME
// ============================================

async function joinGame(roomCode) {
    if (!roomCode) {
        const input = document.getElementById('room-code-input');
        roomCode = input?.value?.trim()?.toUpperCase();
    }

    if (!roomCode || roomCode.length !== 6) {
        showToast('Please enter a valid 6-character room code', 'error');
        return;
    }

    try {
        const result = await api.post('/game/join-room', { room_code: roomCode });

        if (result.success) {
            gameState.roomCode = roomCode;

            // Get current user
            const user = await getCurrentUser();

            // Connect socket
            if (!socket) initSocket();

            socket.emit('join_game', {
                room_code: roomCode,
                user_id: user.id,
                username: user.username,
                avatar: user.avatar
            });

            // Show waiting room
            showWaitingRoom(result);
        }
    } catch (error) {
        showToast(error.message || 'Failed to join game', 'error');
    }
}

function showWaitingRoom(data) {
    const container = document.getElementById('game-container');

    container.innerHTML = `
        <div class="waiting-room">
            <h1>🎮 Get Ready!</h1>
            <p>Joined: <strong>${data.room.quiz_title}</strong></p>
            <p>Host: ${data.room.host_name}</p>
            
            <div class="join-code">${gameState.roomCode}</div>
            
            <div class="glass-card mt-xl">
                <h3>Players in Room</h3>
                <div class="participants-grid" id="participants-grid">
                    ${renderParticipants(data.participants)}
                </div>
                <p class="participant-count mt-lg">
                    <span id="participant-count">${data.participant_count}</span> player(s) ready
                </p>
            </div>
            
            <p class="mt-xl opacity-75">Waiting for host to start the game...</p>
        </div>
    `;

    // Start polling for participant updates
    startPlayerParticipantRefresh();
}

function startPlayerParticipantRefresh() {
    // Clear any existing interval
    if (participantRefreshInterval) {
        clearInterval(participantRefreshInterval);
    }

    // Poll every 1 second
    participantRefreshInterval = setInterval(async () => {
        try {
            const result = await api.get(`/game/room/${gameState.roomCode}`);
            if (result.success && result.participants) {
                const grid = document.getElementById('participants-grid');
                const count = document.getElementById('participant-count');

                if (grid) {
                    grid.innerHTML = renderParticipants(result.participants);
                }

                if (count) {
                    count.textContent = result.participants.length;
                }
            }
        } catch (error) {
            console.error('Failed to fetch participants:', error);
        }
    }, 1000);
}

function stopPlayerParticipantRefresh() {
    if (participantRefreshInterval) {
        clearInterval(participantRefreshInterval);
        participantRefreshInterval = null;
    }
}

function renderParticipants(participants) {
    return participants.map(p => `
        <div class="participant-card">
            <div class="avatar">${getAvatarEmoji(p.avatar)}</div>
            <p>${escapeHtml(p.username)}</p>
        </div>
    `).join('');
}

// ============================================
// SOCKET EVENT HANDLERS
// ============================================

function handlePlayerJoined(data) {
    const grid = document.getElementById('participants-grid');
    const count = document.getElementById('participant-count');

    if (grid && data.players) {
        grid.innerHTML = renderParticipants(data.players);
    }

    if (count) {
        count.textContent = data.player_count;
    }

    showToast(`${data.username} joined!`, 'info');
}

function handlePlayerLeft(data) {
    const count = document.getElementById('participant-count');
    if (count) {
        count.textContent = data.player_count;
    }
    showToast(`${data.username} left`, 'info');
}

async function handleGameStarted() {
    stopPlayerParticipantRefresh();
    showToast('Game is starting!', 'success');

    // Show countdown
    await showStartCountdown();

    // Load questions
    try {
        const result = await api.get(`/game/questions/${gameState.roomCode}`);
        gameState.questions = result.questions;
        gameState.currentQuestion = 0;

        // Show first question
        showQuestion();
    } catch (error) {
        showToast('Failed to load questions', 'error');
    }
}

function handleNewQuestion(data) {
    gameState.hasAnswered = false;
    gameState.timeLeft = 30;

    // Store questions from host if received
    if (data.question) {
        // Store the current question in gameState.questions array
        const questionIndex = data.question_number - 1;
        if (!gameState.questions[questionIndex]) {
            gameState.questions[questionIndex] = data.question;
        }
        gameState.currentQuestion = questionIndex;

        showQuestionFromData(data.question, data.question_number, data.total_questions);
    }
}

function handleLeaderboardUpdate(data) {
    // Show leaderboard when host broadcasts it
    showLeaderboard(data.leaderboard);
}

function handleGameEnded(data) {
    // Only end game if student has finished or this is a forced end
    clearInterval(timerInterval);

    // If we have a final leaderboard, show final results
    if (data.final_leaderboard && data.final_leaderboard.length > 0) {
        showFinalResults(data.final_leaderboard);
    } else {
        // Fetch final results from server
        fetchAndShowFinalResults();
    }
}

async function fetchAndShowFinalResults() {
    try {
        const result = await api.get(`/game/leaderboard/${gameState.roomCode}`);
        showFinalResults(result.leaderboard || []);
    } catch (error) {
        console.error('Failed to fetch final results:', error);
        showFinalResults([]);
    }
}

function handleAnswerReceived(data) {
    // For host view - not used in student view
}

// ============================================
// COUNTDOWN ANIMATION
// ============================================

function showStartCountdown() {
    return new Promise((resolve) => {
        const container = document.getElementById('game-container');

        const overlay = document.createElement('div');
        overlay.className = 'countdown-overlay';
        overlay.innerHTML = '<div class="countdown-number">3</div>';
        container.appendChild(overlay);

        let count = 3;
        const interval = setInterval(() => {
            count--;
            if (count > 0) {
                overlay.querySelector('.countdown-number').textContent = count;
                overlay.querySelector('.countdown-number').style.animation = 'none';
                overlay.offsetHeight; // Trigger reflow
                overlay.querySelector('.countdown-number').style.animation = 'countdownPulse 1s ease-in-out';
            } else {
                overlay.querySelector('.countdown-number').textContent = 'GO!';
                setTimeout(() => {
                    overlay.remove();
                    resolve();
                }, 500);
                clearInterval(interval);
            }
        }, 1000);
    });
}

// ============================================
// QUESTION DISPLAY
// ============================================

function showQuestion() {
    if (gameState.currentQuestion >= gameState.questions.length) {
        showFinalResults();
        return;
    }

    const question = gameState.questions[gameState.currentQuestion];
    showQuestionFromData(question, gameState.currentQuestion + 1, gameState.questions.length);
}

function showQuestionFromData(question, questionNum, totalQuestions) {
    const container = document.getElementById('game-container');
    gameState.hasAnswered = false;
    gameState.timeLeft = 30;

    let answersHtml = '';

    if (question.type === 'mcq') {
        const options = typeof question.options === 'string'
            ? JSON.parse(question.options)
            : question.options;

        answersHtml = `
            <div class="answers-grid">
                ${options.map((opt, i) => `
                    <button class="answer-option" data-answer="${escapeHtml(opt)}" onclick="selectAnswer(this)">
                        ${escapeHtml(opt)}
                        <span class="answer-icon"></span>
                    </button>
                `).join('')}
            </div>
        `;
    } else if (question.type === 'truefalse') {
        answersHtml = `
            <div class="tf-options">
                <button class="answer-option tf-option true" data-answer="true" onclick="selectAnswer(this)">
                    ✓ True
                </button>
                <button class="answer-option tf-option false" data-answer="false" onclick="selectAnswer(this)">
                    ✕ False
                </button>
            </div>
        `;
    } else {
        answersHtml = `
            <div class="short-answer-container">
                <input type="text" class="form-input short-answer-input" id="short-answer" 
                       placeholder="Type your answer..." autocomplete="off">
                <button class="btn btn-primary btn-lg mt-lg w-full" onclick="submitShortAnswer()">
                    Submit Answer
                </button>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="game-header glass">
            <div class="question-progress">
                <span class="question-number">Question ${questionNum} of ${totalQuestions}</span>
                <div class="progress-dots">
                    ${Array(totalQuestions).fill(0).map((_, i) => {
        let dotClass = '';
        if (i < gameState.currentQuestion) dotClass = 'answered';
        if (i === gameState.currentQuestion) dotClass = 'current';
        return `<div class="progress-dot ${dotClass}"></div>`;
    }).join('')}
                </div>
            </div>
            <div class="question-timer">
                <div class="timer-circle" id="timer-circle" style="--progress: 100%">
                    <span class="timer-value" id="timer-value">${gameState.timeLeft}</span>
                </div>
            </div>
        </div>
        
        <div class="question-container animate-slide-up">
            <div class="question-card">
                <span class="question-type-badge">${question.type.toUpperCase()}</span>
                <p class="question-text">${escapeHtml(question.question_text)}</p>
            </div>
            
            ${answersHtml}
        </div>
        
        <div class="game-footer glass mt-xl">
            <div class="flex justify-between items-center">
                <div>
                    <span class="badge badge-primary">Score: ${gameState.score}</span>
                    ${gameState.streak > 0 ? `<span class="badge badge-warning ml-sm">🔥 ${gameState.streak} Streak</span>` : ''}
                </div>
            </div>
        </div>
    `;

    // Start timer
    startTimer();
}

// ============================================
// TIMER
// ============================================

function startTimer() {
    clearInterval(timerInterval);

    const startTime = Date.now();
    const duration = 30000; // 30 seconds

    timerInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, Math.ceil((duration - elapsed) / 1000));

        gameState.timeLeft = remaining;

        const timerValue = document.getElementById('timer-value');
        const timerCircle = document.getElementById('timer-circle');

        if (timerValue) {
            timerValue.textContent = remaining;

            // Add warning classes
            timerValue.classList.remove('timer-warning', 'timer-critical');
            if (remaining <= 5) {
                timerValue.classList.add('timer-critical');
            } else if (remaining <= 10) {
                timerValue.classList.add('timer-warning');
            }
        }

        if (timerCircle) {
            const progress = (remaining / 30) * 100;
            timerCircle.style.setProperty('--progress', `${progress}%`);
        }

        if (remaining <= 0) {
            clearInterval(timerInterval);
            if (!gameState.hasAnswered) {
                timeUp();
            }
        }
    }, 100);
}

function timeUp() {
    gameState.hasAnswered = true;
    showFeedback(false, null, "Time's up!");

    setTimeout(() => {
        nextQuestion();
    }, 2000);
}

// ============================================
// ANSWER HANDLING
// ============================================

async function selectAnswer(button) {
    if (gameState.hasAnswered) return;
    gameState.hasAnswered = true;

    clearInterval(timerInterval);

    const answer = button.dataset.answer;
    const timeTaken = 30 - gameState.timeLeft;

    // Disable all options
    document.querySelectorAll('.answer-option').forEach(opt => {
        opt.classList.add('disabled');
    });

    button.classList.add('selected');

    // Check answer
    try {
        const question = gameState.questions[gameState.currentQuestion];

        // Validate question exists and has ID
        if (!question || !question.id) {
            console.error('Question not found in gameState:', gameState.currentQuestion, gameState.questions);
            showToast('Question data not available, skipping...', 'warning');
            setTimeout(() => nextQuestion(), 2000);
            return;
        }

        const result = await api.post('/game/submit-answer', {
            room_code: gameState.roomCode,
            question_id: question.id,
            answer: answer,
            time_taken: timeTaken
        });

        // Update score
        if (result.is_correct) {
            gameState.score += result.points;
            gameState.streak++;
            button.classList.add('correct');
            button.querySelector('.answer-icon').textContent = '✓';
        } else {
            gameState.streak = 0;
            button.classList.add('incorrect');
            button.querySelector('.answer-icon').textContent = '✕';

            // Show correct answer
            document.querySelectorAll('.answer-option').forEach(opt => {
                if (opt.dataset.answer.toLowerCase() === result.correct_answer.toLowerCase()) {
                    opt.classList.add('correct');
                }
            });
        }

        // Emit to socket
        socket.emit('submit_answer', {
            room_code: gameState.roomCode,
            user_id: currentUser?.id,
            username: currentUser?.username,
            answer: answer,
            time_taken: timeTaken,
            is_correct: result.is_correct,
            points: result.points
        });

        // Show feedback
        showFeedback(result.is_correct, result.points, null, result.streak_bonus);

        setTimeout(() => {
            nextQuestion();
        }, 2000);

    } catch (error) {
        console.error('Failed to submit answer:', error);
        showToast('Failed to submit answer, moving to next question...', 'warning');

        // Continue game even if submission fails
        gameState.streak = 0;
        button.classList.add('incorrect');
        const answerIcon = button.querySelector('.answer-icon');
        if (answerIcon) answerIcon.textContent = '?';

        setTimeout(() => {
            nextQuestion();
        }, 2000);
    }
}

async function submitShortAnswer() {
    const input = document.getElementById('short-answer');
    if (!input || !input.value.trim()) {
        showToast('Please enter an answer', 'warning');
        return;
    }

    // Create a fake button to use selectAnswer logic
    const fakeButton = document.createElement('button');
    fakeButton.dataset.answer = input.value.trim();
    fakeButton.querySelector = () => ({ textContent: '' });
    fakeButton.classList = { add: () => { }, remove: () => { } };

    gameState.hasAnswered = true;
    clearInterval(timerInterval);

    try {
        const question = gameState.questions[gameState.currentQuestion];
        const timeTaken = 30 - gameState.timeLeft;

        const result = await api.post('/game/submit-answer', {
            room_code: gameState.roomCode,
            question_id: question.id,
            answer: input.value.trim(),
            time_taken: timeTaken
        });

        if (result.is_correct) {
            gameState.score += result.points;
            gameState.streak++;
        } else {
            gameState.streak = 0;
        }

        showFeedback(result.is_correct, result.points, `Correct answer: ${result.correct_answer}`);

        setTimeout(() => {
            nextQuestion();
        }, 2000);

    } catch (error) {
        showToast('Failed to submit answer', 'error');
    }
}

// ============================================
// FEEDBACK & TRANSITIONS
// ============================================

function showFeedback(isCorrect, points, message, streakBonus = 0) {
    const overlay = document.createElement('div');
    overlay.className = 'feedback-overlay';

    overlay.innerHTML = `
        <div class="feedback-content ${isCorrect ? 'feedback-correct' : 'feedback-incorrect'}">
            <div class="feedback-icon">${isCorrect ? '✓' : '✕'}</div>
            <p class="feedback-text">${isCorrect ? 'Correct!' : (message || 'Wrong!')}</p>
            ${points ? `<p class="feedback-points">+${points} points</p>` : ''}
            ${streakBonus > 0 ? `<span class="streak-bonus">🔥 +${streakBonus} Streak Bonus!</span>` : ''}
        </div>
    `;

    document.body.appendChild(overlay);

    if (isCorrect) {
        showConfetti();
    }

    setTimeout(() => {
        overlay.remove();
    }, 2000);
}

function nextQuestion() {
    gameState.currentQuestion++;

    if (gameState.currentQuestion >= gameState.questions.length) {
        // Request leaderboard
        socket.emit('show_leaderboard', { room_code: gameState.roomCode });
        showLeaderboard();
    } else {
        showQuestion();
    }
}

// ============================================
// LEADERBOARD
// ============================================

async function showLeaderboard(leaderboard = null) {
    if (!leaderboard) {
        try {
            const result = await api.get(`/game/leaderboard/${gameState.roomCode}`);
            leaderboard = result.leaderboard;
        } catch (error) {
            leaderboard = [];
        }
    }

    const container = document.getElementById('game-container');

    container.innerHTML = `
        <div class="leaderboard-container">
            <div class="leaderboard-title">
                <h2>🏆 Leaderboard</h2>
            </div>
            
            <ul class="leaderboard-list">
                ${leaderboard.map((player, i) => `
                    <li class="leaderboard-item ${i === 0 ? 'top-1' : ''} ${i === 1 ? 'top-2' : ''} ${i === 2 ? 'top-3' : ''}">
                        <div class="leaderboard-position">
                            ${i < 3 ? ['🥇', '🥈', '🥉'][i] : i + 1}
                        </div>
                        <div class="leaderboard-info">
                            <div class="avatar avatar-sm">${getAvatarEmoji(player.avatar)}</div>
                            <span class="leaderboard-name">${escapeHtml(player.username)}</span>
                            ${player.rank_badge ? `<span>${player.rank_badge}</span>` : ''}
                        </div>
                        <div class="leaderboard-score">${player.score}</div>
                    </li>
                `).join('')}
            </ul>
            
            <div class="text-center mt-2xl">
                <p class="opacity-75">Your Score: ${gameState.score}</p>
            </div>
        </div>
    `;

    // Wait a bit then check if game should continue or end
    setTimeout(() => {
        if (gameState.currentQuestion < gameState.questions.length) {
            showQuestion();
        }
    }, 5000);
}

// ============================================
// FINAL RESULTS
// ============================================

function showFinalResults(finalLeaderboard = null) {
    const container = document.getElementById('game-container');

    const winner = finalLeaderboard?.[0];
    const myPosition = finalLeaderboard?.findIndex(p => p.user_id === currentUser?.id) + 1 || 0;

    container.innerHTML = `
        <div class="results-container">
            <div class="results-header">
                <div class="trophy-icon">🏆</div>
                <h1 class="results-title gradient-text">Game Complete!</h1>
                <p class="results-subtitle">Great job everyone!</p>
            </div>
            
            ${winner ? `
                <div class="winner-card">
                    <div class="avatar winner-avatar">${getAvatarEmoji(winner.avatar)}</div>
                    <h2 class="winner-name">${escapeHtml(winner.username)}</h2>
                    <p>Winner! 🎉</p>
                    <div class="winner-score">${winner.score} pts</div>
                </div>
            ` : ''}
            
            <div class="glass-card">
                <h3>Your Results</h3>
                <div class="grid grid-3 mt-lg">
                    <div class="stat-card">
                        <div class="stat-value">${gameState.score}</div>
                        <div class="stat-label">Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">#${myPosition || '?'}</div>
                        <div class="stat-label">Position</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">+${Math.floor(gameState.score / 10)}</div>
                        <div class="stat-label">XP Earned</div>
                    </div>
                </div>
                
                <div class="xp-earned mt-lg">
                    <span>✨</span> You earned XP!
                </div>
            </div>
            
            <div class="mt-2xl">
                <a href="/client/home" class="btn btn-primary btn-lg">Back to Home</a>
            </div>
        </div>
    `;

    showConfetti();

    // Add XP
    if (currentUser) {
        api.post('/auth/add-xp', { xp: Math.floor(gameState.score / 10) });
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Check if there's a room code in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const roomCode = urlParams.get('room') || window.ROOM_CODE;

    if (roomCode) {
        initSocket();
        joinGame(roomCode);
    }
});
