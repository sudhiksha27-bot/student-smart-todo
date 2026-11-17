"""
Database connection and abstraction layer for Smart To-Do List Assistant.
Supports:
1. Native MySQL via `mysql-connector-python`
2. Automatic fallback to local SQLite if MySQL server is offline,
   allowing instant zero-friction demonstration without breaking functionality.
3. Automatically creates tables and seeds sample data if empty.
"""

import os
import re
import datetime
from datetime import datetime as dt, timedelta
import sqlite3

try:
    import mysql.connector
    from mysql.connector import errorcode
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


# Database Configuration (can be overridden via environment variables)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'smart_todo')

# Active connection mode: 'mysql' or 'sqlite'
DB_MODE = None
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smart_todo.db')


class SQLiteCursorWrapper:
    """Wrapper around sqlite3 cursor to transparently adapt MySQL queries (%s placeholders, dict return)."""
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        # Convert MySQL %s placeholders to SQLite ? placeholders
        sqlite_query = query.replace('%s', '?')
        
        # Replace MySQL specific functions if any
        # DATE_SUB(NOW(), INTERVAL X DAY/HOUR)
        # SQLite uses datetime('now', '-X days')
        def replace_date_sub(match):
            val = match.group(1)
            unit = match.group(2).lower()
            if not unit.endswith('s'):
                unit += 's'
            return f"datetime('now', '-{val} {unit}')"

        def replace_date_add(match):
            val = match.group(1)
            unit = match.group(2).lower()
            if not unit.endswith('s'):
                unit += 's'
            return f"datetime('now', '+{val} {unit}')"

        sqlite_query = re.sub(r"DATE_SUB\s*\(\s*NOW\(\)\s*,\s*INTERVAL\s+(\d+)\s+([A-Za-z]+)\s*\)", replace_date_sub, sqlite_query, flags=re.IGNORECASE)
        sqlite_query = re.sub(r"DATE_ADD\s*\(\s*NOW\(\)\s*,\s*INTERVAL\s+(\d+)\s+([A-Za-z]+)\s*\)", replace_date_add, sqlite_query, flags=re.IGNORECASE)
        sqlite_query = re.sub(r"\bNOW\(\)", "datetime('now')", sqlite_query, flags=re.IGNORECASE)

        if params:
            # Convert booleans or datetime objects if needed
            converted_params = []
            for p in params:
                if isinstance(p, (dt, datetime.date)):
                    converted_params.append(p.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    converted_params.append(p)
            return self.cursor.execute(sqlite_query, converted_params)
        return self.cursor.execute(sqlite_query)

    def executemany(self, query, seq_of_params):
        sqlite_query = query.replace('%s', '?')
        return self.cursor.executemany(sqlite_query, seq_of_params)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()


class DBConnection:
    """Unified database connection wrapper for MySQL and SQLite."""
    def __init__(self, mode, raw_conn):
        self.mode = mode
        self.raw_conn = raw_conn

    def cursor(self, dictionary=True):
        if self.mode == 'mysql':
            return self.raw_conn.cursor(dictionary=dictionary)
        else:
            raw_cur = self.raw_conn.cursor()
            return SQLiteCursorWrapper(raw_cur)

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()


def test_mysql_connection():
    """Attempt a direct connection to MySQL server."""
    if not MYSQL_AVAILABLE:
        return False, "mysql-connector-python is not installed."
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3
        )
        conn.close()
        return True, "MySQL connection successful."
    except Exception as e:
        return False, str(e)


def init_mysql_db():
    """Create MySQL database and tables if they do not exist."""
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_NAME}")

    # Read and execute schema.sql
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        statements = sql_script.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.lower().startswith('create database') and not stmt.lower().startswith('use '):
                try:
                    cursor.execute(stmt)
                except Exception as ex:
                    print(f"[MySQL Init Warning] {ex}")

    # Check if tasks table is populated
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed.sql')
        if os.path.exists(seed_path):
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed_script = f.read()
            for stmt in seed_script.split(';'):
                stmt = stmt.strip()
                if stmt and not stmt.lower().startswith('use ') and not stmt.lower().startswith('set '):
                    try:
                        cursor.execute(stmt)
                    except Exception as ex:
                        print(f"[MySQL Seed Warning] {ex}")
    conn.commit()
    cursor.close()
    conn.close()


def init_sqlite_db():
    """Initialize local SQLite database with the exact same schema and seed data."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        color TEXT DEFAULT '#4F46E5',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'Medium',
        due_date TEXT NOT NULL,
        estimated_minutes INTEGER DEFAULT 30,
        status TEXT DEFAULT 'Pending',
        created_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
    CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
    CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        now = dt.now()
        cursor.execute("INSERT OR IGNORE INTO users (id, name, email, created_at) VALUES (1, 'Alex Morgan', 'alex.morgan@university.edu', ?)",
                       (now.strftime('%Y-%m-%d %H:%M:%S'),))

        categories = [
            (1, 1, 'Core CS & Algorithms', '#6366F1'),
            (2, 1, 'Web & Full Stack', '#06B6D4'),
            (3, 1, 'Mathematics & Stats', '#10B981'),
            (4, 1, 'Database Systems', '#F59E0B'),
            (5, 1, 'Career & Capstone', '#EC4899')
        ]
        cursor.executemany("INSERT OR IGNORE INTO categories (id, user_id, name, color) VALUES (?, ?, ?, ?)", categories)

        tasks = [
            # 1. Overdue High
            (1, 1, 1, 'Prepare for CS301 Midterm Exam', 'Review dynamic programming, recursion trees, and greedy graph heuristics.', 'High',
             (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 120, 'Pending', (now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 2. Overdue Medium
            (2, 1, 4, 'Submit SQL Optimization Homework', 'Write EXPLAIN ANALYZE queries on composite B-Tree indexes.', 'Medium',
             (now - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S'), 45, 'In Progress', (now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 3. Due Today High
            (3, 1, 2, 'Fix Authentication Bug in Flask App', 'Token expiry issue in session cookie causing intermittent 401 errors.', 'High',
             (now + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'), 60, 'Pending', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 4. Due Today Medium
            (4, 1, 3, 'Linear Algebra Problem Set #4', 'Eigenvalues, eigenvectors, and singular value decomposition exercises.', 'Medium',
             (now + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'), 90, 'Pending', (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 5. Due Today Low
            (5, 1, 5, 'Update LinkedIn Profile & Project Links', 'Add GitHub repositories for Capstone project and link live demo.', 'Low',
             (now + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S'), 20, 'Pending', (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 6. Due Tomorrow High
            (6, 1, 1, 'Implement Red-Black Tree Deletion', 'Finish C++ implementation of node rebalancing cases 1 through 4.', 'High',
             (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 90, 'Pending', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 7. Due Tomorrow Medium
            (7, 1, 2, 'Design Responsive CSS Dashboard Grid', 'Use modern CSS Grid and Flexbox with responsive breakpoints for tablet and mobile.', 'Medium',
             (now + timedelta(days=1, hours=4)).strftime('%Y-%m-%d %H:%M:%S'), 45, 'In Progress', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), None),
            # 8. Due in 2 days
            (8, 1, 4, 'Normalize Database Schema to 3NF', 'Eliminate transitive dependencies in student enrollment schema draft.', 'Medium',
             (now + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), 60, 'Pending', now.strftime('%Y-%m-%d %H:%M:%S'), None),
            # 9. Due in 3 days High
            (9, 1, 5, 'Draft Software Engineering Internship Resume', 'Tailor bullet points to emphasize MySQL, Python Flask, and REST API development.', 'High',
             (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'), 75, 'Pending', now.strftime('%Y-%m-%d %H:%M:%S'), None),
            # 10. Due in 4 days Low
            (10, 1, 3, 'Review Probability Density Functions', 'Read Chapter 6 of textbook and summarize Chebyshev bounds.', 'Low',
             (now + timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S'), 30, 'Pending', now.strftime('%Y-%m-%d %H:%M:%S'), None),
            # 11. Due in 5 days Medium
            (11, 1, 2, 'Build RESTful API Endpoints for Tasks', 'Implement CRUD controllers with json responses and error handlers.', 'Medium',
             (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'), 60, 'Pending', now.strftime('%Y-%m-%d %H:%M:%S'), None),
            # 12. Due in 7 days Low
            (12, 1, 5, 'Schedule Capstone Mentorship Meeting', 'Email faculty mentor with sprint progress and agenda items.', 'Low',
             (now + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'), 15, 'Pending', now.strftime('%Y-%m-%d %H:%M:%S'), None),
            # 13. Completed High
            (13, 1, 1, 'Solve LeetCode Top 50 Graph Problems', 'Completed BFS, DFS, Dijkstra, and Topological Sort challenges.', 'High',
             (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 90, 'Completed', (now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
             (now - timedelta(hours=18)).strftime('%Y-%m-%d %H:%M:%S')),
            # 14. Completed Medium
            (14, 1, 4, 'Set Up Local MySQL 8.0 Instance', 'Configured database credentials, created database users and tables.', 'Medium',
             (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), 30, 'Completed', (now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S'),
             (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')),
            # 15. Completed Low
            (15, 1, 3, 'Watch Calculus II Lecture Recording', 'Watched integration by parts and trigonometric substitution recap.', 'Low',
             (now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'), 45, 'Completed', (now - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
             (now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'))
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO tasks 
        (id, user_id, category_id, title, description, priority, due_date, estimated_minutes, status, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tasks)

    conn.commit()
    conn.close()


def get_connection():
    """Returns a connected DBConnection instance (MySQL if running, else SQLite fallback)."""
    global DB_MODE
    mysql_ok, msg = test_mysql_connection()
    if mysql_ok:
        try:
            raw_conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            DB_MODE = 'mysql'
            return DBConnection('mysql', raw_conn)
        except Exception as e:
            # If database doesn't exist yet, try to initialize it
            try:
                init_mysql_db()
                raw_conn = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME
                )
                DB_MODE = 'mysql'
                return DBConnection('mysql', raw_conn)
            except Exception as e2:
                print(f"[Database Warning] MySQL connection failed ({e2}). Falling back to SQLite.")

    # SQLite fallback
    DB_MODE = 'sqlite'
    if not os.path.exists(SQLITE_PATH):
        init_sqlite_db()
    raw_conn = sqlite3.connect(SQLITE_PATH)
    raw_conn.row_factory = sqlite3.Row
    return DBConnection('sqlite', raw_conn)


def get_db_info():
    """Return database runtime information for the UI badge and diagnostics."""
    conn = get_connection()
    mode = conn.mode
    conn.close()
    return {
        'mode': mode,
        'label': 'MySQL (Connected)' if mode == 'mysql' else 'Local DB (MySQL Ready)',
        'database': DB_NAME,
        'host': DB_HOST if mode == 'mysql' else 'smart_todo.db'
    }


# Auto-initialize database on module import
try:
    mysql_ok, _ = test_mysql_connection()
    if mysql_ok:
        init_mysql_db()
    else:
        init_sqlite_db()
except Exception as e:
    init_sqlite_db()

