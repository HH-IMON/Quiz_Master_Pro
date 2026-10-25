# Quiz Master Pro - System Diagrams

## 1. High-Level Architecture

```mermaid
flowchart TB
    subgraph "Client Layer"
        A["🌐 Web Browser"]
    end

    subgraph "Presentation Layer"
        B["📄 HTML Templates"]
        C["🎨 CSS (style.css)"]
        D["⚡ JavaScript (app.js, auth.js)"]
    end

    subgraph "Application Layer"
        E["🐍 Flask App (app.py)"]
        F["🔌 Flask-SocketIO"]
        subgraph "API Routes (Blueprints)"
            G1["auth.py"]
            G2["quiz.py"]
            G3["game.py"]
            G4["practice.py"]
            G5["battle.py"]
            G6["chat.py"]
            G7["admin.py"]
            G8["exam.py"]
            G9["questions.py"]
        end
    end

    subgraph "Data Layer"
        H["💾 MySQL Database (XAMPP)"]
    end

    A <--> B
    B --> C
    B --> D
    A <--> E
    A <--> F
    E --> G1 & G2 & G3 & G4 & G5 & G6 & G7 & G8 & G9
    G1 & G2 & G3 & G4 & G5 & G6 & G7 & G8 & G9 --> H
```

---

## 2. Data Flow Diagram (DFD) - Level 0

```mermaid
flowchart LR
    subgraph External["External Entities"]
        S["👨‍🎓 Student"]
        T["👨‍🏫 Teacher"]
        AD["🔧 Admin"]
    end

    subgraph System["Quiz Master Pro System"]
        QMP["📊 Quiz Master Pro"]
    end

    subgraph Data["Data Stores"]
        DB["💾 MySQL Database"]
    end

    S -->|"Register/Login, Submit Answers, Join Game"| QMP
    QMP -->|"Quiz Questions, Scores, Leaderboard"| S

    T -->|"Create Quiz, Host Game, View Results"| QMP
    QMP -->|"Quiz Data, Game Status, Analytics"| T

    AD -->|"Manage Users, Categories, System Config"| QMP
    QMP -->|"User List, System Stats"| AD

    QMP <-->|"Read/Write"| DB
```

---

## 3. Data Flow Diagram (DFD) - Level 1

```mermaid
flowchart TB
    subgraph Entities["External Entities"]
        S["👨‍🎓 Student"]
        T["👨‍🏫 Teacher"]
        AD["🔧 Admin"]
    end

    subgraph Processes["Processes"]
        P1["1.0 Authentication"]
        P2["2.0 Quiz Management"]
        P3["3.0 Live Game"]
        P4["4.0 Practice Mode"]
        P5["5.0 Battle Mode"]
        P6["6.0 Exam System"]
        P7["7.0 Chat System"]
        P8["8.0 Admin Panel"]
    end

    subgraph DataStores["Data Stores"]
        D1["D1: users"]
        D2["D2: quizzes"]
        D3["D3: questions"]
        D4["D4: game_rooms"]
        D5["D5: practice_progress"]
        D6["D6: battle_matches"]
        D7["D7: exams"]
        D8["D8: chat_messages"]
    end

    %% Student flows
    S --> P1 --> D1
    S --> P3 --> D4
    S --> P4 --> D5
    S --> P5 --> D6
    S --> P6 --> D7
    S --> P7 --> D8

    %% Teacher flows
    T --> P1
    T --> P2 --> D2
    P2 --> D3
    T --> P3
    T --> P6

    %% Admin flows
    AD --> P8 --> D1
    P8 --> D2
```

---

## 4. Use Case Diagram

```mermaid
flowchart LR
    subgraph Actors
        Student["👨‍🎓 Student"]
        Teacher["👨‍🏫 Teacher"]
        Admin["🔧 Admin"]
    end

    subgraph UseCases["Quiz Master Pro"]
        UC1["Register/Login"]
        UC2["Join Live Quiz Game"]
        UC3["Practice Mode"]
        UC4["1v1 Battle Mode"]
        UC5["Take Exam"]
        UC6["View Leaderboard"]
        UC7["Chat/Discussion"]
        UC8["View Profile & XP"]
        UC9["Create/Edit Quiz"]
        UC10["Manage Question Bank"]
        UC11["Host Live Game"]
        UC12["Create/Schedule Exams"]
        UC13["View Results/Analytics"]
        UC14["Manage Users"]
        UC15["Manage Categories"]
        UC16["System Analytics"]
        
        %% Helper Use Cases
        UC_AUTH([Authenticate])
        UC_VAL([Validate Code])
    end

    %% Student use cases
    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8

    %% Teacher use cases
    Teacher --> UC1
    Teacher --> UC10
    Teacher --> UC11
    Teacher --> UC12
    Teacher --> UC13
    Teacher --> UC14

    %% Admin use cases
    Admin --> UC1
    Admin --> UC15
    Admin --> UC16
    Admin --> UC17

    %% Include/Extend Relationships
    UC2 -.->|<<include>>| UC_VAL
    UC1 -.->|<<include>>| UC_AUTH
    UC5 -.->|<<extend>>| UC14
    UC12 -.->|<<include>>| UC10
```

---

## 5. Sequence Diagram - Live Quiz Game Flow

```mermaid
sequenceDiagram
    participant S as Student
    participant B as Browser
    participant WS as WebSocket (SocketIO)
    participant App as Flask App
    participant DB as MySQL

    Note over S, DB: Teacher hosts game first

    S->>B: Enter Room Code
    B->>WS: emit("join_game", {room_code, user_id})
    WS->>App: handle_join_game()
    App->>DB: Verify room exists
    
    alt Room Exists
        DB-->>App: Room data found
        App->>DB: Add participant
        DB-->>App: Success
        App->>WS: join_room(room_code)
        WS->>B: emit("player_joined")
        B-->>S: Show Waiting Screen
    else Room Not Found
        DB-->>App: None
        App->>WS: emit("error", {msg: "Invalid Room"})
        WS->>B: emit("error", "Invalid Room")
        B-->>S: Show Error Message
    end

    Note over S, DB: Host starts game

    WS->>B: emit("game_started")
    B-->>S: Show Game UI

    loop Each Question
        WS->>B: emit("new_question", {question_data})
        B-->>S: Display Question + Timer
        S->>B: Select Answer
        B->>WS: emit("submit_answer", {answer, time})
        WS->>App: handle_submit_answer()
        App->>DB: Record answer, calculate score
        DB-->>App: Updated score
        App->>WS: emit("answer_received")
        WS->>B: emit("show_leaderboard")
    end

    WS->>B: emit("game_ended", {final_results})
    App->>DB: Save quiz_results, update XP
    B-->>S: Show Final Results
```

---

## 6. Database ER Diagram

```mermaid
erDiagram
    USERS ||--o{ QUIZZES : creates
    USERS ||--o{ GAME_ROOMS : hosts
    USERS ||--o{ GAME_PARTICIPANTS : joins
    USERS ||--o{ PRACTICE_PROGRESS : has
    USERS ||--o{ BATTLE_MATCHES : plays
    USERS ||--o{ QUIZ_RESULTS : earns
    USERS ||--o{ EXAM_SUBMISSIONS : submits
    USERS ||--o{ CHAT_MESSAGES : sends

    CATEGORIES ||--o{ QUIZZES : contains
    CATEGORIES ||--o{ PRACTICE_PROGRESS : tracks

    QUIZZES ||--o{ QUESTIONS : has
    QUIZZES ||--o{ GAME_ROOMS : used_in
    QUIZZES ||--o{ EXAMS : based_on

    GAME_ROOMS ||--o{ GAME_PARTICIPANTS : has

    EXAMS ||--o{ EXAM_SUBMISSIONS : receives

    CHAT_ROOMS ||--o{ CHAT_MESSAGES : contains

    USERS {
        int id PK
        string username
        string email
        string password_hash
        enum role
        int xp_points
        int level
    }

    QUIZZES {
        int id PK
        string title
        int category_id FK
        int created_by FK
        enum difficulty
    }

    QUESTIONS {
        int id PK
        int quiz_id FK
        enum type
        text question_text
        json options
        string correct_answer
    }

    GAME_ROOMS {
        int id PK
        string room_code
        int quiz_id FK
        int host_id FK
        enum status
    }

    EXAMS {
        int id PK
        string title
        int quiz_id FK
        datetime start_time
        datetime end_time
    }
```

---

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python Flask |
| Real-time | Flask-SocketIO (WebSockets) |
| Database | MySQL (via XAMPP) |
| Authentication | Session-based with password hashing |
| Styling | Custom CSS with Glassmorphism design |
