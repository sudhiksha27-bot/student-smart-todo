"""
Smart To-Do List Assistant - Flask Web Application
Backend with MySQL connector, Smart Assistant features, NLP task parser,
Auto-priority engine, and productivity analytics.
"""

import os
import sys
import re
from datetime import datetime, timedelta

# Ensure application directory is in python search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from flask import Flask, render_template, request, jsonify

from db import get_connection, get_db_info

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'student-smart-todo-secret-key-2026')


# -----------------------------------------------------------------------------
# HELPER: Format task dictionary for JSON response
# -----------------------------------------------------------------------------
def format_task(task):
    if not task:
        return None
    # Parse due_date to ISO string if needed
    due_date = task.get('due_date')
    if isinstance(due_date, datetime):
        due_str = due_date.strftime('%Y-%m-%d %H:%M:%S')
        due_iso = due_date.isoformat()
    elif due_date:
        due_str = str(due_date)
        due_iso = str(due_date).replace(' ', 'T')
    else:
        due_str = None
        due_iso = None

    # Check overdue / due today relative to current time
    now = datetime.now()
    is_overdue = False
    is_due_today = False

    if due_date:
        try:
            if isinstance(due_date, str):
                parsed_due = datetime.strptime(due_date[:19], '%Y-%m-%d %H:%M:%S' if ' ' in due_date else '%Y-%m-%dT%H:%M:%S')
            else:
                parsed_due = due_date

            if task.get('status') != 'Completed':
                if parsed_due < now:
                    is_overdue = True
                elif parsed_due.date() == now.date():
                    is_due_today = True
        except Exception:
            pass

    return {
        'id': task.get('id'),
        'user_id': task.get('user_id'),
        'category_id': task.get('category_id'),
        'category_name': task.get('category_name') or 'Uncategorized',
        'category_color': task.get('category_color') or '#64748B',
        'title': task.get('title'),
        'description': task.get('description') or '',
        'priority': task.get('priority') or 'Medium',
        'due_date': due_str,
        'due_date_iso': due_iso,
        'estimated_minutes': task.get('estimated_minutes') or 30,
        'status': task.get('status') or 'Pending',
        'created_at': str(task.get('created_at')) if task.get('created_at') else None,
        'completed_at': str(task.get('completed_at')) if task.get('completed_at') else None,
        'is_overdue': is_overdue,
        'is_due_today': is_due_today
    }


# -----------------------------------------------------------------------------
# NLP SMART PARSER FOR NATURAL LANGUAGE ADD
# Examples:
# "Submit report tomorrow 5pm high priority"
# "Prepare math quiz on Friday 10am 45m"
# "Review chapter 4 tonight 8pm urgent"
# -----------------------------------------------------------------------------
def parse_natural_language_task(nl_text):
    text = nl_text.strip()
    now = datetime.now()
    
    # 1. Detect Priority
    priority = 'Medium'
    if re.search(r'\b(high|urgent|critical|exam|midterm|final|asap|important)\b', text, re.IGNORECASE):
        priority = 'High'
    elif re.search(r'\b(low|casual|optional|minor|someday)\b', text, re.IGNORECASE):
        priority = 'Low'

    # Remove priority keywords from clean title
    clean_text = re.sub(r'\b(high\s+priority|medium\s+priority|low\s+priority|high|urgent|critical|asap)\b', '', text, flags=re.IGNORECASE)

    # 2. Detect Estimated Minutes
    estimated_minutes = 30
    duration_match = re.search(r'(\d+)\s*(mins?|minutes?|m)\b', text, re.IGNORECASE)
    if duration_match:
        estimated_minutes = int(duration_match.group(1))
        clean_text = re.sub(r'(\d+)\s*(mins?|minutes?|m)\b', '', clean_text, flags=re.IGNORECASE)
    else:
        hour_match = re.search(r'(\d+(\.\d+)?)\s*(hours?|hrs?|h)\b', text, re.IGNORECASE)
        if hour_match:
            estimated_minutes = int(float(hour_match.group(1)) * 60)
            clean_text = re.sub(r'(\d+(\.\d+)?)\s*(hours?|hrs?|h)\b', '', clean_text, flags=re.IGNORECASE)

    # 3. Detect Due Date & Time
    target_date = now.date()
    target_time = datetime.strptime("17:00", "%H:%M").time()  # default 5:00 PM

    # Date keywords
    if re.search(r'\btomorrow\b', text, re.IGNORECASE):
        target_date = now.date() + timedelta(days=1)
        clean_text = re.sub(r'\btomorrow\b', '', clean_text, flags=re.IGNORECASE)
    elif re.search(r'\btoday\b', text, re.IGNORECASE):
        target_date = now.date()
        clean_text = re.sub(r'\btoday\b', '', clean_text, flags=re.IGNORECASE)
    elif re.search(r'\btonight\b', text, re.IGNORECASE):
        target_date = now.date()
        target_time = datetime.strptime("21:00", "%H:%M").time()
        clean_text = re.sub(r'\btonight\b', '', clean_text, flags=re.IGNORECASE)
    else:
        # Check weekdays: monday, tuesday, etc.
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for idx, day in enumerate(days_of_week):
            match = re.search(rf'\b(next\s+)?{day}\b', text, re.IGNORECASE)
            if match:
                current_weekday = now.weekday()
                days_ahead = (idx - current_weekday) % 7
                if days_ahead == 0 or match.group(1):
                    days_ahead += 7
                target_date = now.date() + timedelta(days=days_ahead)
                clean_text = re.sub(rf'\b(next\s+)?{day}\b', '', clean_text, flags=re.IGNORECASE)
                break

    # Time keywords e.g. "5pm", "5:30pm", "10am", "20:00"
    time_match = re.search(r'\b(at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', text, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(2))
        minute = int(time_match.group(3)) if time_match.group(3) else 0
        ampm = time_match.group(4).lower()
        if ampm == 'pm' and hour < 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        target_time = datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()
        clean_text = re.sub(r'\b(at\s+)?\d{1,2}(?::\d{2})?\s*(am|pm)\b', '', clean_text, flags=re.IGNORECASE)

    due_datetime = datetime.combine(target_date, target_time)

    # 4. Clean Title
    title = re.sub(r'\s+', ' ', clean_text).strip(' ,.-')
    if not title:
        title = "New Task"

    # 5. Smart Category Matching
    category_id = 1
    lower_title = title.lower()
    if any(k in lower_title for k in ['sql', 'database', 'db', 'schema', 'query', '3nf']):
        category_id = 4
    elif any(k in lower_title for k in ['web', 'html', 'css', 'flask', 'api', 'react', 'js', 'frontend', 'auth']):
        category_id = 2
    elif any(k in lower_title for k in ['math', 'calculus', 'algebra', 'stats', 'probability', 'eigen']):
        category_id = 3
    elif any(k in lower_title for k in ['resume', 'career', 'interview', 'linkedin', 'capstone', 'meeting', 'internship']):
        category_id = 5
    elif any(k in lower_title for k in ['cs', 'algorithm', 'tree', 'code', 'leetcode', 'program', 'graph']):
        category_id = 1

    return {
        'title': title.capitalize(),
        'priority': priority,
        'due_date': due_datetime.strftime('%Y-%m-%d %H:%M:%S'),
        'estimated_minutes': estimated_minutes,
        'category_id': category_id,
        'description': f"Auto-generated from quick prompt: \"{nl_text}\""
    }


# -----------------------------------------------------------------------------
# AUTO-PRIORITY ENGINE
# Evaluates deadline urgency and keywords to suggest Low / Medium / High
# -----------------------------------------------------------------------------
def calculate_auto_priority(title, due_date_str):
    now = datetime.now()
    urgent_keywords = ['urgent', 'exam', 'midterm', 'final', 'quiz', 'critical', 'asap', 'presentation', 'interview', 'test', 'deadline']
    low_keywords = ['read', 'browse', 'review', 'podcast', 'clean', 'optional', 'casual', 'ideas', 'later', 'someday']

    title_lower = title.lower()
    has_urgent_keyword = any(k in title_lower for k in urgent_keywords)
    has_low_keyword = any(k in title_lower for k in low_keywords)

    hours_until_due = 9999
    if due_date_str:
        try:
            if 'T' in due_date_str:
                due = datetime.strptime(due_date_str[:16], '%Y-%m-%dT%H:%M')
            else:
                due = datetime.strptime(due_date_str[:19], '%Y-%m-%d %H:%M:%S')
            diff = due - now
            hours_until_due = diff.total_seconds() / 3600.0
        except Exception:
            pass

    if hours_until_due < 24 or has_urgent_keyword:
        return 'High', 'Urgent deadline within 24 hours or exam/critical keywords detected.'
    elif hours_until_due > 120 and has_low_keyword:
        return 'Low', 'Due date is over 5 days away with flexible/reading keywords.'
    elif hours_until_due < 72:
        return 'Medium', 'Due within 3 days. Standard student priority.'
    else:
        return 'Medium', 'Standard priority assigned.'


# -----------------------------------------------------------------------------
# ROUTES: Page Views
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


# -----------------------------------------------------------------------------
# API: Database Info & Diagnostics
# -----------------------------------------------------------------------------
@app.route('/api/db-info', methods=['GET'])
def db_info_endpoint():
    return jsonify(get_db_info())


# -----------------------------------------------------------------------------
# API: Categories
# -----------------------------------------------------------------------------
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    # SQL JOIN & GROUP BY for category counts
    cur.execute("""
        SELECT c.id, c.name, c.color, 
               COUNT(t.id) as total_tasks,
               SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks
        FROM categories c
        LEFT JOIN tasks t ON c.id = t.category_id
        GROUP BY c.id, c.name, c.color
        ORDER BY c.id ASC
    """)
    categories = cur.fetchall()
    conn.close()
    return jsonify(categories)


# -----------------------------------------------------------------------------
# API: Tasks List with Filter and Search (MySQL JOIN, WHERE, ORDER BY)
# -----------------------------------------------------------------------------
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    category_id = request.args.get('category_id')
    priority = request.args.get('priority')
    status = request.args.get('status')
    due_filter = request.args.get('due_filter')  # 'overdue', 'today', 'upcoming'
    search = request.args.get('search')
    sort_by = request.args.get('sort_by', 'priority_due')

    query = """
        SELECT t.*, c.name AS category_name, c.color AS category_color, u.name AS user_name
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    """
    params = []

    if category_id and category_id.isdigit():
        query += " AND t.category_id = %s"
        params.append(int(category_id))

    if priority and priority in ['Low', 'Medium', 'High']:
        query += " AND t.priority = %s"
        params.append(priority)

    if status and status in ['Pending', 'In Progress', 'Completed']:
        query += " AND t.status = %s"
        params.append(status)

    if search:
        query += " AND (t.title LIKE %s OR t.description LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    now = datetime.now()
    if due_filter == 'overdue':
        query += " AND t.status != 'Completed' AND t.due_date < %s"
        params.append(now.strftime('%Y-%m-%d %H:%M:%S'))
    elif due_filter == 'today':
        today_start = now.strftime('%Y-%m-%d 00:00:00')
        today_end = now.strftime('%Y-%m-%d 23:59:59')
        query += " AND t.status != 'Completed' AND t.due_date >= %s AND t.due_date <= %s"
        params.extend([today_start, today_end])
    elif due_filter == 'upcoming':
        today_end = now.strftime('%Y-%m-%d 23:59:59')
        query += " AND t.status != 'Completed' AND t.due_date > %s"
        params.append(today_end)

    # Sorting
    if sort_by == 'due_date':
        query += " ORDER BY t.due_date ASC"
    elif sort_by == 'priority':
        query += " ORDER BY FIELD(t.priority, 'High', 'Medium', 'Low'), t.due_date ASC"
    elif sort_by == 'title':
        query += " ORDER BY t.title ASC"
    else: # priority_due
        # Prioritize In Progress/Pending, High Priority, Nearest Due Date
        query += """
            ORDER BY 
              CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END ASC,
              CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END ASC,
              t.due_date ASC
        """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    raw_tasks = cur.fetchall()
    conn.close()

    formatted = [format_task(t) for t in raw_tasks]
    return jsonify(formatted)


# -----------------------------------------------------------------------------
# API: Add Task
# -----------------------------------------------------------------------------
@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Task title is required.'}), 400

    user_id = data.get('user_id', 1)
    category_id = data.get('category_id') or None
    description = data.get('description', '').strip()
    priority = data.get('priority', 'Medium')
    due_date = data.get('due_date')
    estimated_minutes = int(data.get('estimated_minutes', 30))
    status = data.get('status', 'Pending')

    if not due_date:
        # Default due tomorrow at 5pm
        due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 17:00:00')

    # Convert ISO to SQL datetime if needed
    due_date = due_date.replace('T', ' ')
    if len(due_date) == 16:
        due_date += ':00'

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks 
        (user_id, category_id, title, description, priority, due_date, estimated_minutes, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, (user_id, category_id, title, description, priority, due_date, estimated_minutes, status))
    task_id = cur.lastrowid
    conn.commit()

    # Fetch inserted task with joins
    cur.execute("""
        SELECT t.*, c.name AS category_name, c.color AS category_color, u.name AS user_name
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = %s
    """, (task_id,))
    task = cur.fetchone()
    conn.close()

    return jsonify({'message': 'Task created successfully', 'task': format_task(task)}), 201


# -----------------------------------------------------------------------------
# API: Edit Task
# -----------------------------------------------------------------------------
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Task title is required.'}), 400

    category_id = data.get('category_id') or None
    description = data.get('description', '').strip()
    priority = data.get('priority', 'Medium')
    due_date = data.get('due_date')
    estimated_minutes = int(data.get('estimated_minutes', 30))
    status = data.get('status', 'Pending')

    due_date = due_date.replace('T', ' ') if due_date else datetime.now().strftime('%Y-%m-%d 17:00:00')
    if len(due_date) == 16:
        due_date += ':00'

    completed_at = None
    if status == 'Completed':
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks 
        SET category_id = %s,
            title = %s,
            description = %s,
            priority = %s,
            due_date = %s,
            estimated_minutes = %s,
            status = %s,
            completed_at = CASE WHEN %s = 'Completed' AND completed_at IS NULL THEN NOW()
                                WHEN %s != 'Completed' THEN NULL
                                ELSE completed_at END
        WHERE id = %s
    """, (category_id, title, description, priority, due_date, estimated_minutes, status, status, status, task_id))
    conn.commit()

    cur.execute("""
        SELECT t.*, c.name AS category_name, c.color AS category_color, u.name AS user_name
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = %s
    """, (task_id,))
    task = cur.fetchone()
    conn.close()

    return jsonify({'message': 'Task updated successfully', 'task': format_task(task)})


# -----------------------------------------------------------------------------
# API: Mark Task Status (Toggle complete / progress)
# -----------------------------------------------------------------------------
@app.route('/api/tasks/<int:task_id>/status', methods=['PATCH'])
def toggle_task_status(task_id):
    data = request.json or {}
    new_status = data.get('status')
    if new_status not in ['Pending', 'In Progress', 'Completed']:
        return jsonify({'error': 'Invalid status.'}), 400

    conn = get_connection()
    cur = conn.cursor()

    if new_status == 'Completed':
        cur.execute("UPDATE tasks SET status = %s, completed_at = NOW() WHERE id = %s", (new_status, task_id))
    else:
        cur.execute("UPDATE tasks SET status = %s, completed_at = NULL WHERE id = %s", (new_status, task_id))

    conn.commit()

    cur.execute("""
        SELECT t.*, c.name AS category_name, c.color AS category_color, u.name AS user_name
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = %s
    """, (task_id,))
    task = cur.fetchone()
    conn.close()

    return jsonify({'message': f'Task status updated to {new_status}', 'task': format_task(task)})


# -----------------------------------------------------------------------------
# API: Delete Task
# -----------------------------------------------------------------------------
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    if affected == 0:
        return jsonify({'error': 'Task not found.'}), 404
    return jsonify({'message': 'Task deleted successfully', 'id': task_id})


# -----------------------------------------------------------------------------
# SMART FEATURE 1: Auto-Priority Suggestion
# -----------------------------------------------------------------------------
@app.route('/api/smart/auto-priority', methods=['POST'])
def auto_priority_endpoint():
    data = request.json or {}
    title = data.get('title', '')
    due_date = data.get('due_date', '')
    priority, reason = calculate_auto_priority(title, due_date)
    return jsonify({
        'suggested_priority': priority,
        'reason': reason
    })


# -----------------------------------------------------------------------------
# SMART FEATURE 2: "What should I do next?" Assistant
# Evaluates priority, deadline urgency, and time estimate to pick optimal task
# -----------------------------------------------------------------------------
@app.route('/api/smart/what-next', methods=['GET'])
def what_next_endpoint():
    focus_mode = request.args.get('mode', 'balanced')  # 'balanced', 'quick_win', 'deep_work'

    conn = get_connection()
    cur = conn.cursor()
    # Fetch all non-completed tasks
    cur.execute("""
        SELECT t.*, c.name AS category_name, c.color AS category_color, u.name AS user_name
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.status != 'Completed'
    """)
    tasks = cur.fetchall()
    conn.close()

    if not tasks:
        return jsonify({
            'has_tasks': False,
            'message': 'All tasks completed! You are completely caught up 🎉'
        })

    now = datetime.now()
    scored_tasks = []

    for t in tasks:
        score = 0
        reasons = []

        # Priority Weight
        prio = t.get('priority')
        if prio == 'High':
            score += 100
            reasons.append("High Priority (+100)")
        elif prio == 'Medium':
            score += 50
            reasons.append("Medium Priority (+50)")
        else:
            score += 20
            reasons.append("Low Priority (+20)")

        # Urgency Weight
        due = t.get('due_date')
        if isinstance(due, str):
            try:
                due = datetime.strptime(due[:19], '%Y-%m-%d %H:%M:%S' if ' ' in due else '%Y-%m-%dT%H:%M:%S')
            except Exception:
                due = now + timedelta(days=2)

        if due < now:
            score += 160
            reasons.append("⚠️ Overdue! Immediate focus recommended (+160)")
        elif due.date() == now.date():
            hours_left = (due - now).total_seconds() / 3600
            if hours_left <= 4:
                score += 120
                reasons.append("🔥 Due in <4 hours today (+120)")
            else:
                score += 90
                reasons.append("⏰ Due today (+90)")
        elif (due - now).total_seconds() <= 86400 * 2:
            score += 60
            reasons.append("📅 Due within 48 hours (+60)")
        else:
            score += 10

        # Status boost (In Progress)
        if t.get('status') == 'In Progress':
            score += 35
            reasons.append("⚡ Already in progress (+35)")

        # Focus Mode Adjustments
        mins = t.get('estimated_minutes') or 30
        if focus_mode == 'quick_win':
            if mins <= 30:
                score += 60
                reasons.append("⚡ Quick win task (≤30m)")
        elif focus_mode == 'deep_work':
            if mins >= 60:
                score += 50
                reasons.append("🧠 Deep work session (≥60m)")

        scored_tasks.append({
            'task': format_task(t),
            'score': score,
            'reason': " • ".join(reasons)
        })

    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    best = scored_tasks[0]
    runner_up = scored_tasks[1] if len(scored_tasks) > 1 else None

    return jsonify({
        'has_tasks': True,
        'best_task': best['task'],
        'recommendation_reason': best['reason'],
        'score': best['score'],
        'runner_up': runner_up['task'] if runner_up else None
    })


# -----------------------------------------------------------------------------
# SMART FEATURE 4: Daily Plan Generator
# Arranges today's tasks into a structured study/work schedule
# -----------------------------------------------------------------------------
@app.route('/api/smart/daily-plan', methods=['GET'])
def generate_daily_plan():
    conn = get_connection()
    cur = conn.cursor()
    # Fetch pending tasks ordered by priority and due date
    cur.execute("""
        SELECT t.*, c.name AS category_name, c.color AS category_color
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.status != 'Completed'
        ORDER BY 
          CASE WHEN t.due_date < NOW() THEN 0 
               WHEN DATE(t.due_date) = DATE(NOW()) THEN 1 
               ELSE 2 END ASC,
          CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END ASC,
          t.due_date ASC
        LIMIT 6
    """)
    tasks = cur.fetchall()
    conn.close()

    if not tasks:
        return jsonify({'schedule': [], 'total_minutes': 0, 'message': 'No pending tasks to schedule.'})

    now = datetime.now()
    # Start schedule from next round hour or current time rounded up
    minute = (now.minute // 15 + 1) * 15
    start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minute)
    if start_time < now:
        start_time += timedelta(minutes=15)

    schedule = []
    current_time = start_time
    total_study_mins = 0

    for i, t in enumerate(tasks):
        duration = t.get('estimated_minutes') or 45
        end_time = current_time + timedelta(minutes=duration)

        schedule.append({
            'start_time': current_time.strftime('%I:%M %p'),
            'end_time': end_time.strftime('%I:%M %p'),
            'duration_minutes': duration,
            'task': format_task(t),
            'type': 'task'
        })
        current_time = end_time
        total_study_mins += duration

        # Add 15 min rest break after deep tasks
        if i < len(tasks) - 1:
            break_mins = 15 if duration >= 60 else 10
            break_end = current_time + timedelta(minutes=break_mins)
            schedule.append({
                'start_time': current_time.strftime('%I:%M %p'),
                'end_time': break_end.strftime('%I:%M %p'),
                'duration_minutes': break_mins,
                'type': 'break',
                'title': 'Coffee & Recharge Break ☕' if break_mins == 15 else 'Quick Stretch 🧘'
            })
            current_time = break_end

    return jsonify({
        'schedule': schedule,
        'total_study_minutes': total_study_mins,
        'total_duration': f"{total_study_mins // 60}h {total_study_mins % 60}m",
        'task_count': len(tasks)
    })


# -----------------------------------------------------------------------------
# SMART FEATURE 6: Natural Language Task Creation
# -----------------------------------------------------------------------------
@app.route('/api/smart/nlp-add', methods=['POST'])
def nlp_add_task():
    data = request.json or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Please provide a task description.'}), 400

    parsed = parse_natural_language_task(prompt)

    # Insert into database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks 
        (user_id, category_id, title, description, priority, due_date, estimated_minutes, status, created_at)
        VALUES (1, %s, %s, %s, %s, %s, %s, 'Pending', NOW())
    """, (
        parsed['category_id'],
        parsed['title'],
        parsed['description'],
        parsed['priority'],
        parsed['due_date'],
        parsed['estimated_minutes']
    ))
    task_id = cur.lastrowid
    conn.commit()

    cur.execute("""
        SELECT t.*, c.name AS category_name, c.color AS category_color, u.name AS user_name
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = %s
    """, (task_id,))
    task = cur.fetchone()
    conn.close()

    return jsonify({
        'message': 'Task created from natural language!',
        'parsed_metadata': parsed,
        'task': format_task(task)
    }), 201


# -----------------------------------------------------------------------------
# SMART FEATURE 5: Productivity Dashboard Analytics (MySQL GROUP BY, JOIN)
# -----------------------------------------------------------------------------
@app.route('/api/stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Overall Task Counters
    cur.execute("""
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_tasks,
            SUM(CASE WHEN status != 'Completed' AND due_date < NOW() THEN 1 ELSE 0 END) as overdue_tasks,
            SUM(CASE WHEN status != 'Completed' AND DATE(due_date) = DATE(NOW()) THEN 1 ELSE 0 END) as due_today_tasks
        FROM tasks
    """)
    overview = cur.fetchone() or {}

    total = overview.get('total_tasks') or 0
    completed = overview.get('completed_tasks') or 0
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    # 2. Priority Distribution (GROUP BY priority)
    cur.execute("""
        SELECT priority, COUNT(*) as count 
        FROM tasks 
        WHERE status != 'Completed' 
        GROUP BY priority
    """)
    priority_rows = cur.fetchall()
    priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for row in priority_rows:
        p = row.get('priority')
        if p in priority_counts:
            priority_counts[p] = row.get('count')

    # 3. Category Distribution (JOIN + GROUP BY)
    cur.execute("""
        SELECT c.id, c.name, c.color, 
               COUNT(t.id) as total,
               SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed
        FROM categories c
        LEFT JOIN tasks t ON c.id = t.category_id
        GROUP BY c.id, c.name, c.color
        ORDER BY total DESC
    """)
    category_stats = cur.fetchall()

    # 4. Weekly Completion Trend (GROUP BY DATE(completed_at))
    cur.execute("""
        SELECT DATE(completed_at) as log_date, COUNT(*) as count
        FROM tasks
        WHERE status = 'Completed' AND completed_at IS NOT NULL
        GROUP BY DATE(completed_at)
        ORDER BY log_date ASC
    """)
    weekly_rows = cur.fetchall()

    conn.close()

    return jsonify({
        'overview': {
            'total': total,
            'completed': completed,
            'in_progress': overview.get('in_progress_tasks') or 0,
            'pending': overview.get('pending_tasks') or 0,
            'overdue': overview.get('overdue_tasks') or 0,
            'due_today': overview.get('due_today_tasks') or 0,
            'completion_rate': completion_rate
        },
        'priority_counts': priority_counts,
        'category_stats': category_stats,
        'weekly_completion': weekly_rows
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Smart To-Do Assistant running at: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
