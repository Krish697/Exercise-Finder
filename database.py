import sqlite3
import os

if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/exercise_finder.db'
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'exercise_finder.db')


def get_db():
    """Open a new database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            gender TEXT
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity TEXT NOT NULL,
            duration INTEGER NOT NULL,
            calories INTEGER NOT NULL,
            sets INTEGER DEFAULT 0,
            reps INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS weight_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            target_value REAL NOT NULL,
            target_date TEXT NOT NULL,
            set_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            exercise_type TEXT,
            muscle TEXT,
            difficulty TEXT,
            instructions TEXT,
            UNIQUE(user_id, exercise_name),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')

    conn.commit()
    conn.close()


# ─── User helpers ───────────────────────────────────────────────────────────

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user


def create_user(username, email, password_hash):
    conn = get_db()
    conn.execute(
        'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
        (username, email, password_hash)
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    """Permanently delete a user and all cascade data."""
    conn = get_db()
    conn.execute('DELETE FROM history WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM weight_log WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM goals WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM favourites WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()


def update_profile(user_id, username, age, height, weight, gender):
    conn = get_db()
    old = conn.execute('SELECT weight FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.execute(
        'UPDATE users SET username=?, age=?, height=?, weight=?, gender=? WHERE id=?',
        (username, age, height, weight, gender, user_id)
    )
    # Log weight if it changed
    if old and old['weight'] != weight and weight:
        conn.execute(
            'INSERT INTO weight_log (user_id, weight) VALUES (?, ?)',
            (user_id, weight)
        )
    conn.commit()
    conn.close()


# ─── History helpers ─────────────────────────────────────────────────────────

def add_history(user_id, activity, duration, calories, sets=0, reps=0):
    conn = get_db()
    conn.execute(
        'INSERT INTO history (user_id, activity, duration, calories, sets, reps) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, activity, duration, calories, sets, reps)
    )
    conn.commit()
    conn.close()


def get_history(user_id, query=None):
    conn = get_db()
    if query:
        rows = conn.execute(
            'SELECT * FROM history WHERE user_id=? AND activity LIKE ? ORDER BY timestamp DESC',
            (user_id, f'%{query}%')
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM history WHERE user_id=? ORDER BY timestamp DESC',
            (user_id,)
        ).fetchall()
    conn.close()
    return rows


def get_progress_stats(user_id):
    conn = get_db()
    total_workouts = conn.execute(
        'SELECT COUNT(*) as cnt FROM history WHERE user_id=?', (user_id,)
    ).fetchone()['cnt']

    total_minutes = conn.execute(
        'SELECT SUM(duration) as s FROM history WHERE user_id=?', (user_id,)
    ).fetchone()['s'] or 0

    total_calories = conn.execute(
        'SELECT SUM(calories) as s FROM history WHERE user_id=?', (user_id,)
    ).fetchone()['s'] or 0

    most_common = conn.execute(
        'SELECT activity, COUNT(*) as cnt FROM history WHERE user_id=? GROUP BY activity ORDER BY cnt DESC LIMIT 1',
        (user_id,)
    ).fetchone()

    conn.close()
    return {
        'total_workouts': total_workouts,
        'total_minutes': total_minutes,
        'total_calories': total_calories,
        'most_common': most_common['activity'] if most_common else 'N/A'
    }


# ─── Weight log helpers ──────────────────────────────────────────────────────

def get_weight_log(user_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT weight, logged_at FROM weight_log WHERE user_id=? ORDER BY logged_at ASC',
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


# ─── Goals helpers ───────────────────────────────────────────────────────────

def add_goal(user_id, category, target_value, target_date):
    conn = get_db()
    conn.execute(
        'INSERT INTO goals (user_id, category, target_value, target_date) VALUES (?, ?, ?, ?)',
        (user_id, category, target_value, target_date)
    )
    conn.commit()
    conn.close()


def get_goals(user_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM goals WHERE user_id=? ORDER BY set_at DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_recent_goal(user_id):
    """Return the most recently set goal."""
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM goals WHERE user_id=? ORDER BY set_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    conn.close()
    return row


# ─── Favourites helpers ──────────────────────────────────────────────────────

def add_favourite(user_id, exercise_name, exercise_type, muscle, difficulty, instructions):
    conn = get_db()
    try:
        conn.execute(
            '''INSERT OR IGNORE INTO favourites
               (user_id, exercise_name, exercise_type, muscle, difficulty, instructions)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, exercise_name, exercise_type, muscle, difficulty, instructions)
        )
        conn.commit()
        added = conn.execute('SELECT changes() as c').fetchone()['c']
    except Exception:
        added = 0
    conn.close()
    return added > 0


def remove_favourite(user_id, exercise_name):
    conn = get_db()
    conn.execute(
        'DELETE FROM favourites WHERE user_id=? AND exercise_name=?',
        (user_id, exercise_name)
    )
    conn.commit()
    conn.close()


def get_favourites(user_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM favourites WHERE user_id=? ORDER BY id DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def is_favourite(user_id, exercise_name):
    conn = get_db()
    row = conn.execute(
        'SELECT id FROM favourites WHERE user_id=? AND exercise_name=?',
        (user_id, exercise_name)
    ).fetchone()
    conn.close()
    return row is not None
