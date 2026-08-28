import os
from supabase import create_client, Client
from collections import Counter

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# ── Singleton client (create once, reuse across all requests) ──────────────
_db_client: Client | None = None

def get_db() -> Client:
    """Return a shared Supabase client (singleton for performance)."""
    global _db_client
    if _db_client is None:
        _db_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _db_client


def init_db():
    """No-op: Tables are managed via supabase_migration.sql in Supabase."""
    pass


# ─── User helpers ─────────────────────────────────────────────────────────────

def get_user_by_email(email):
    db = get_db()
    result = db.table('users').select('*').eq('email', email).execute()
    return result.data[0] if result.data else None


def get_user_by_id(user_id):
    db = get_db()
    result = db.table('users').select('*').eq('id', user_id).execute()
    return result.data[0] if result.data else None


def create_user(username, email, password_hash):
    db = get_db()
    db.table('users').insert({
        'username': username,
        'email': email,
        'password_hash': password_hash
    }).execute()


def delete_user(user_id):
    """Permanently delete a user — cascade handled by FK ON DELETE CASCADE."""
    db = get_db()
    db.table('users').delete().eq('id', user_id).execute()


def update_profile(user_id, username, age, height, weight, gender):
    db = get_db()
    old = get_user_by_id(user_id)
    db.table('users').update({
        'username': username,
        'age': age,
        'height': height,
        'weight': weight,
        'gender': gender
    }).eq('id', user_id).execute()
    # Log weight if it changed
    if old and old.get('weight') != weight and weight:
        db.table('weight_log').insert({
            'user_id': user_id,
            'weight': weight
        }).execute()


# ─── History helpers ──────────────────────────────────────────────────────────

def add_history(user_id, activity, duration, calories, sets=0, reps=0):
    db = get_db()
    db.table('history').insert({
        'user_id': user_id,
        'activity': activity,
        'duration': duration,
        'calories': calories,
        'sets': sets,
        'reps': reps
    }).execute()


def delete_history_item(user_id, item_id):
    """Delete a history entry only if it belongs to the given user."""
    db = get_db()
    db.table('history').delete().eq('id', item_id).eq('user_id', user_id).execute()


def get_history(user_id, query=None):
    db = get_db()
    q = db.table('history').select('*').eq('user_id', user_id)
    if query:
        q = q.ilike('activity', f'%{query}%')
    result = q.order('timestamp', desc=True).execute()
    return result.data


def get_progress_stats(user_id):
    db = get_db()
    history = db.table('history').select('activity,duration,calories').eq('user_id', user_id).execute().data
    total_workouts = len(history)
    total_minutes = sum(h.get('duration', 0) or 0 for h in history)
    total_calories = sum(h.get('calories', 0) or 0 for h in history)
    activities = [h['activity'] for h in history]
    most_common = Counter(activities).most_common(1)[0][0] if activities else 'N/A'
    return {
        'total_workouts': total_workouts,
        'total_minutes': total_minutes,
        'total_calories': total_calories,
        'most_common': most_common
    }


# ─── Weight log helpers ───────────────────────────────────────────────────────

def get_weight_log(user_id):
    db = get_db()
    result = db.table('weight_log').select('weight,logged_at').eq('user_id', user_id).order('logged_at').execute()
    return result.data


# ─── Goals helpers ────────────────────────────────────────────────────────────

def add_goal(user_id, category, target_value, target_date):
    db = get_db()
    db.table('goals').insert({
        'user_id': user_id,
        'category': category,
        'target_value': target_value,
        'target_date': target_date
    }).execute()


def delete_goal(user_id, goal_id):
    """Delete a goal only if it belongs to the given user."""
    db = get_db()
    db.table('goals').delete().eq('id', goal_id).eq('user_id', user_id).execute()


def get_goals(user_id):
    db = get_db()
    result = db.table('goals').select('*').eq('user_id', user_id).order('set_at', desc=True).execute()
    return result.data


def get_recent_goal(user_id):
    """Return the most recently set goal."""
    db = get_db()
    result = db.table('goals').select('*').eq('user_id', user_id).order('set_at', desc=True).limit(1).execute()
    return result.data[0] if result.data else None


# ─── Favourites helpers ───────────────────────────────────────────────────────

def add_favourite(user_id, exercise_name, exercise_type, muscle, difficulty, instructions):
    db = get_db()
    try:
        existing = db.table('favourites').select('id').eq('user_id', user_id).eq('exercise_name', exercise_name).execute()
        if existing.data:
            return False
        db.table('favourites').insert({
            'user_id': user_id,
            'exercise_name': exercise_name,
            'exercise_type': exercise_type,
            'muscle': muscle,
            'difficulty': difficulty,
            'instructions': instructions
        }).execute()
        return True
    except Exception:
        return False


def remove_favourite(user_id, exercise_name):
    db = get_db()
    db.table('favourites').delete().eq('user_id', user_id).eq('exercise_name', exercise_name).execute()


def get_favourites(user_id):
    db = get_db()
    result = db.table('favourites').select('*').eq('user_id', user_id).order('id', desc=True).execute()
    return result.data


def is_favourite(user_id, exercise_name):
    db = get_db()
    result = db.table('favourites').select('id').eq('user_id', user_id).eq('exercise_name', exercise_name).execute()
    return len(result.data) > 0


# ─── Workout Plans helpers (NEW) ──────────────────────────────────────────────

def add_workout_plan(user_id, name, description, exercises, ai_generated=False):
    """Save a workout plan (AI or manual) as a JSON array of exercises."""
    db = get_db()
    result = db.table('workout_plans').insert({
        'user_id': user_id,
        'name': name,
        'description': description,
        'exercises': exercises,
        'ai_generated': ai_generated
    }).execute()
    return result.data[0] if result.data else None


def get_workout_plans(user_id):
    db = get_db()
    result = db.table('workout_plans').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
    return result.data


def get_workout_plan(plan_id, user_id):
    db = get_db()
    result = db.table('workout_plans').select('*').eq('id', plan_id).eq('user_id', user_id).execute()
    return result.data[0] if result.data else None


def delete_workout_plan(plan_id, user_id):
    db = get_db()
    db.table('workout_plans').delete().eq('id', plan_id).eq('user_id', user_id).execute()


def update_workout_plan_exercises(plan_id, user_id, exercises):
    """Persist updated checklist state (checked/unchecked exercises)."""
    db = get_db()
    db.table('workout_plans').update({'exercises': exercises}).eq('id', plan_id).eq('user_id', user_id).execute()


# ─── Admin helpers ────────────────────────────────────────────────────────────

def get_all_table_data():
    """Fetch all rows from every table for the admin dashboard."""
    db = get_db()
    tables = ['users', 'history', 'weight_log', 'goals', 'favourites', 'workout_plans']
    data = {}
    for t in tables:
        result = db.table(t).select('*').execute()
        data[t] = result.data
    return data
