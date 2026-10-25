# Quiz Master Pro

A modern, full-stack real-time quiz platform featuring a glassmorphism design, live game modes, and distinct portals for teachers and students.

## 🚀 Features

- **Server Portal** (Teacher/Admin):
  - Create and manage quizzes/questions
  - Host live Kahoot-style games
  - View analytics and results
  - Admin dashboard for user management

- **Client Portal** (Student):
  - Join live games via room code
  - Practice mode with progress tracking
  - 1v1 Battle mode
  - Real-time chat and leaderboard
  - Profile customization with XP system

- **UI/UX**:
  - Glassmorphism design system
  - Animated backgrounds and particles
  - Real-time updates via WebSockets

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- XAMPP (for MySQL database)

### Installation

1. **Database Setup**:
   - Start MySQL and Apache in the XAMPP Control Panel.
   - Creates a database named `quizmasterpro` automatically on first run.

2. **Install Dependencies**:
   ```bash
   pip install flask flask-socketio flask-cors mysql-connector-python
   ```
   *(Note: `eventlet` is NOT required and may cause issues on newer Python versions on Windows. We use threading mode for development.)*

3. **Run the Server**:
   ```bash
   python app.py
   ```

## 🌐 Accessing the App

Once running, access the application at:

- **Landing Page**: http://localhost:5000/
- **Student Login**: http://localhost:5000/client/login
- **Teacher Login**: http://localhost:5000/server/login

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`

## 📁 Project Structure

```
quizmasterpero/
├── app.py              # Main application entry point
├── config.py           # Configuration settings
├── database.py         # Database connection and schema
├── routes/             # Route blueprints
│   ├── auth.py         # Authentication logic
│   ├── game.py         # Game room management
│   ├── ...             # Other route modules
├── static/
│   ├── css/            # Stylesheets (Glassmorphism)
│   ├── js/             # Client-side logic
├── templates/
│   ├── client/         # Student portal templates
│   ├── server/         # Teacher/Admin portal templates
│   └── index.html      # Landing page
```
