"""
Quiz Master Pro - Database Module
MySQL database connection and schema initialization for XAMPP
"""
import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
            **Config.DB_SSL
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize the database and create all tables"""
    try:
        # Try connecting to the specific database first (Cloud/Production case)
        connection = None
        try:
            connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                **Config.DB_SSL
            )
            print(f"Connected directly to database '{Config.DB_NAME}'")
        except Error as e:
            # If database doesn't exist, try connecting without DB to create it (Local/XAMPP case)
            print(f"Database '{Config.DB_NAME}' not found or accessible directly. Attempting to create...")
            connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                port=Config.DB_PORT,
                **Config.DB_SSL
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
            cursor.execute(f"USE {Config.DB_NAME}")
            cursor.close()

        cursor = connection.cursor()
        
        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'teacher', 'student') DEFAULT 'student',
                avatar VARCHAR(50) DEFAULT 'avatar1',
                xp_points INT DEFAULT 0,
                level INT DEFAULT 1,
                rank_badge VARCHAR(10) DEFAULT '🌱',
                is_online BOOLEAN DEFAULT FALSE,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                icon VARCHAR(50) DEFAULT '📚',
                color VARCHAR(20) DEFAULT '#667eea'
            )
        """)
        
        # Create Quizzes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                category_id INT,
                created_by INT,
                difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
                time_per_question INT DEFAULT 30,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                quiz_id INT NOT NULL,
                type ENUM('mcq', 'truefalse', 'short') DEFAULT 'mcq',
                question_text TEXT NOT NULL,
                options JSON,
                correct_answer VARCHAR(500) NOT NULL,
                explanation TEXT,
                points INT DEFAULT 10,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )
        """)
        
        # Create Game Rooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_code VARCHAR(10) UNIQUE NOT NULL,
                quiz_id INT NOT NULL,
                host_id INT NOT NULL,
                status ENUM('waiting', 'active', 'paused', 'ended') DEFAULT 'waiting',
                current_question INT DEFAULT 0,
                started_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
                FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create Game Participants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_participants (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                user_id INT NOT NULL,
                score INT DEFAULT 0,
                streak INT DEFAULT 0,
                current_position INT DEFAULT 0,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES game_rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create Chat Rooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type ENUM('public', 'private', 'quiz_discussion') DEFAULT 'public',
                quiz_id INT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create Chat Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                sender_id INT NOT NULL,
                message TEXT NOT NULL,
                message_type ENUM('text', 'question', 'answer') DEFAULT 'text',
                parent_message_id INT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_message_id) REFERENCES chat_messages(id) ON DELETE SET NULL
            )
        """)
        
        # Create Practice Progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS practice_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                category_id INT NOT NULL,
                questions_attempted INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                wrong_questions JSON,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_category (user_id, category_id)
            )
        """)
        
        # Create Battle Matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_matches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                battle_type ENUM('1v1', 'team') DEFAULT '1v1',
                quiz_id INT,
                question_ids JSON,
                player1_id INT NOT NULL,
                player2_id INT,
                player1_score INT DEFAULT 0,
                player2_score INT DEFAULT 0,
                winner_id INT,
                status ENUM('waiting', 'active', 'completed') DEFAULT 'waiting',
                match_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL,
                FOREIGN KEY (player1_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (player2_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (winner_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create Quiz Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                quiz_id INT NOT NULL,
                score INT DEFAULT 0,
                total_questions INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                time_taken INT DEFAULT 0,
                completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )
        """)
        
        # Create Exams table for scheduled exams
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                quiz_id INT,
                created_by INT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                duration_minutes INT DEFAULT 60,
                is_active BOOLEAN DEFAULT TRUE,
                show_results BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create Exam Submissions table for student submissions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_submissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                exam_id INT NOT NULL,
                user_id INT NOT NULL,
                answers JSON,
                score INT DEFAULT 0,
                total_questions INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                submitted_at DATETIME,
                status ENUM('in_progress', 'submitted', 'expired') DEFAULT 'in_progress',
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY unique_exam_user (exam_id, user_id)
            )
        """)
        
        # Insert default categories
        cursor.execute("""
            INSERT IGNORE INTO categories (id, name, description, icon, color) VALUES
            (1, 'Mathematics', 'Numbers, algebra, geometry and more', '🔢', '#667eea'),
            (2, 'Science', 'Physics, chemistry, biology', '🔬', '#00d4aa'),
            (3, 'History', 'World history and events', '📜', '#feca57'),
            (4, 'Geography', 'Countries, capitals, maps', '🌍', '#4facfe'),
            (5, 'Languages', 'Grammar, vocabulary, literature', '📖', '#f093fb'),
            (6, 'Technology', 'Computers, programming, IT', '💻', '#ff9500'),
            (7, 'General Knowledge', 'Miscellaneous facts', '🧠', '#a855f7'),
            (8, 'Sports', 'Games, athletes, tournaments', '⚽', '#00f2fe')
        """)
        
        from werkzeug.security import generate_password_hash
        admin_hash = generate_password_hash('admin123')
        
        # Insert default admin user (password: admin123)
        cursor.execute("""
            INSERT IGNORE INTO users (id, username, email, password_hash, role, level, rank_badge) VALUES
            (1, 'admin', 'admin@quizmasterpro.com', %s, 'admin', 7, '💎')
        """, (admin_hash,))
        
        # Insert default public chat room
        cursor.execute("""
            INSERT IGNORE INTO chat_rooms (id, name, type, created_by) VALUES
            (1, 'General Discussion', 'public', 1),
            (2, 'Study Help', 'public', 1),
            (3, 'Quiz Talk', 'public', 1)
        """)
        
        connection.commit()
        print("Database initialized successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"Error initializing database: {e}")
        return False

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = cursor.lastrowid
        
        cursor.close()
        connection.close()
        return result
        
    except Error as e:
        print(f"Error executing query: {e}")
        return None

def execute_many(query, data_list):
    """Execute multiple inserts"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.executemany(query, data_list)
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"Error executing batch query: {e}")
        return False
