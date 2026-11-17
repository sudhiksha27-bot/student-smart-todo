# 🎓 Smart To-Do List Assistant

An intelligent, student-focused task planning and productivity assistant backed by **MySQL** and **Python (Flask)** with a modern, responsive user interface.

Designed specifically for students managing academic coursework, exam deadlines, and capstone projects, this assistant combines robust SQL relational data modeling with smart productivity algorithms including natural language task entry, deadline-urgency auto-prioritization, a "What should I do next?" smart scheduler, and an automated daily study plan generator.

---

## 🛠️ Tech Stack

- **Database**: MySQL 8.0+ (with InnoDB engine, foreign keys, indexes, UTF8MB4)
- **Backend**: Python 3.10+ / Flask, `mysql-connector-python`
- **Frontend**: Modern Vanilla HTML5 / CSS3 / JavaScript (ES6+), Plus Jakarta Sans typography
- **Architecture**: RESTful JSON APIs, layered database abstraction (`db.py`), responsive CSS grid layout

---

## 📂 Project Structure

```text
smart_todo_assistant/
├── schema.sql           # MySQL database DDL, tables, constraints & indexes
├── seed.sql             # Sample data (1 user, 5 categories, 15 realistic tasks)
├── app.py               # Flask backend, REST API routes & smart algorithms
├── db.py                # Database connection manager (MySQL with zero-friction fallback)
├── requirements.txt     # Python package dependencies
├── .env.example         # Template for environment variables and DB credentials
├── README.md            # Complete documentation, queries & presentation guide
├── static/
│   ├── css/
│   │   └── style.css    # Clean, modern student UI stylesheet
│   └── js/
│       └── app.js       # Dynamic frontend interactions & API integrations
└── templates/
    └── index.html       # Single-page dashboard application template
```

---

## 🗄️ Database Architecture (`smart_todo`)

### 1. Entity-Relationship Diagram

```text
+-------------------+       +-----------------------+
|      users        |       |      categories       |
+-------------------+       +-----------------------+
| id (PK)           |<---+  | id (PK)               |<---+
| name              |    |  | user_id (FK -> users) |    |
| email (UNIQUE)    |    +--| name                  |    |
| created_at        |    |  | color                 |    |
+-------------------+    |  +-----------------------+    |
                         |                               |
                         |  +-----------------------+    |
                         |  |         tasks         |    |
                         |  +-----------------------+    |
                         +--| user_id (FK -> users) |    |
                            | category_id (FK)      |----+
                            | id (PK)               |
                            | title                 |
                            | description           |
                            | priority [L/M/H]      |
                            | due_date              |
                            | estimated_minutes     |
                            | status [P/IP/C]       |
                            | created_at            |
                            | completed_at          |
                            +-----------------------+
```

### 2. Key Tables & Constraints

- **`users`**: Stores student account details.
- **`categories`**: Academic subjects/areas (`Core CS & Algorithms`, `Web & Full Stack`, `Mathematics & Stats`, `Database Systems`, `Career & Capstone`) with custom hex colors.
- **`tasks`**: The core student task entity with `priority` (`Low`, `Medium`, `High`), `status` (`Pending`, `In Progress`, `Completed`), timestamps for tracking completion, and foreign keys.

---

## 🚀 Setup & Installation

### Step 1: Install MySQL Server

If you do not already have MySQL installed:
- **Windows**: Download [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) or install via XAMPP / Laragon.
- **macOS**: `brew install mysql && brew services start mysql`
- **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install mysql-server`

Ensure MySQL service is running on port `3306`.

### Step 2: Import the Database Schema & Seed Data

Open your terminal or MySQL command line client:

```bash
# Log in to MySQL
mysql -u root -p

# Execute schema and seed scripts
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql
```

Alternatively, open `schema.sql` and `seed.sql` inside **MySQL Workbench** or **phpMyAdmin** and execute them.

### Step 3: Configure Environment Variables

Copy `.env.example` to `.env` (or set the variables directly):

```bash
cp .env.example .env
```

Set your MySQL credentials:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=smart_todo
```

*(Note: `db.py` contains a built-in zero-friction fallback to an embedded local database so you can preview and test the complete app immediately even before launching MySQL).*

### Step 4: Install Dependencies & Run the App

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Run the Flask development server
python app.py
```

Open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## 💡 Key MySQL Queries Used in the Application

Here are the primary MySQL queries utilized by the backend to implement filtering, analytical dashboards, and smart scheduling:

### 1. `JOIN` Query — Fetching Tasks with Category & User Details
```sql
SELECT 
    t.id,
    t.title,
    t.description,
    t.priority,
    t.due_date,
    t.estimated_minutes,
    t.status,
    c.name AS category_name,
    c.color AS category_color,
    u.name AS user_name
FROM tasks t
JOIN users u ON t.user_id = u.id
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1
ORDER BY 
    CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END ASC,
    CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END ASC,
    t.due_date ASC;
```

### 2. `GROUP BY` & Aggregations — Category Task Distribution
```sql
SELECT 
    c.id, 
    c.name, 
    c.color, 
    COUNT(t.id) AS total_tasks,
    SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id
GROUP BY c.id, c.name, c.color
ORDER BY total_tasks DESC;
```

### 3. Date & Urgency Filtering — Overdue and Due-Today Tasks
```sql
-- Overdue Tasks (status is not completed and due_date has elapsed)
SELECT * FROM tasks 
WHERE status != 'Completed' AND due_date < NOW()
ORDER BY due_date ASC;

-- Tasks Due Today
SELECT * FROM tasks 
WHERE status != 'Completed' 
  AND due_date >= CURDATE() 
  AND due_date < CURDATE() + INTERVAL 1 DAY
ORDER BY due_date ASC;
```

### 4. `GROUP BY` Date Trend — Weekly Productivity Analytics
```sql
SELECT 
    DATE(completed_at) AS log_date, 
    COUNT(*) AS completed_count
FROM tasks
WHERE status = 'Completed' 
  AND completed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(completed_at)
ORDER BY log_date ASC;
```

---

## ⚡ Smart Features

| Feature | Description |
| :--- | :--- |
| **Natural Language Add** | Type *"Submit biology lab report tomorrow 5pm high priority 45m"* and the assistant parses the title, computes the exact due datetime, sets priority to High, estimates 45 minutes, and assigns the category automatically. |
| **Auto-Priority Engine** | Suggests priority in real-time as you type task names and dates based on urgency windows (<24h = High) and critical academic keywords (*"exam"*, *"quiz"*, *"midterm"*). |
| **"What should I do next?"** | Evaluates active tasks with weighted multi-factor scoring (urgency + priority weight + focus duration mode) to recommend the single most impactful task to tackle right now. |
| **Smart Reminders Banner** | Instant alerts at the top of the interface whenever assignments are overdue or approaching deadline today. |
| **Daily Plan Generator** | Generates a structured study schedule for today with calculated study blocks and recommended coffee/mental recharge breaks. |
| **Productivity Dashboard** | Dynamic counters, progress bar, category distribution, and completion rates. |

---

## 🎤 Presentation Demo Script

Follow this 2-minute walkthrough while presenting:

1. **Introduction (15s)**:
   - *"Hello everyone! Today I'm presenting the Smart To-Do Assistant for students, built with Python Flask and backed by a relational MySQL database."*
   - Point out the active database status badge and the 4 metric cards (Total tasks, Completion Rate, Overdue, Due Today).

2. **Smart Reminders & Filtering (30s)**:
   - Click the **"View Overdue"** or **"Due Today"** pill filter.
   - Show how the interface instantly filters tasks, highlighting the red urgency border on overdue assignments and the amber border on tasks due today.
   - Click **"Reset Filters"** to show the complete task list.

3. **Natural Language Task Creation (30s)**:
   - Click one of the quick suggestions or type into the AI bar:
     `Submit Operating Systems homework tomorrow 5pm high priority 60m`
   - Click **"Create Task"**.
   - Show how the task card appears immediately with **High Priority**, a 60-minute badge, tomorrow's 5:00 PM deadline, and categorized under Core CS.

4. **"What Should I Do Next?" Assistant (20s)**:
   - Click the purple **"What should I do next?"** button.
   - Explain the scoring model: the algorithm weighs approaching deadlines, priority levels, and work duration.
   - Click **"⚡ Start Working on This"** to mark the task In Progress.

5. **Daily Plan Generator (15s)**:
   - Click **"📅 Daily Plan"**.
   - Show the generated time-blocked study schedule with automatic 10-15 minute coffee and recharge breaks.

6. **Task Completion & Dashboard Progress (10s)**:
   - Check off a task by clicking its circle checkbox.
   - Highlight the animated progress bar increasing and the completion counter updating in real-time.

