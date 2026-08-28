import os
import json
import requests
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_from_directory,
                   make_response, Response)
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

import database as db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

API_KEY = os.getenv('API_NINJAS_KEY', '')
API_URL = 'https://api.api-ninjas.com/v1/exercises'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Initialise DB on startup (no-op for Supabase — tables managed via SQL migration)
db.init_db()


# ─── Datetime helper ──────────────────────────────────────────────────────────

def parse_datetime(dt_str):
    """Parse both SQLite ('YYYY-MM-DD HH:MM:SS') and Supabase ISO-8601 timestamps."""
    if not dt_str:
        return None
    try:
        # ISO-8601 with timezone (Supabase)
        if 'T' in str(dt_str):
            dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
            # Strip timezone so arithmetic works uniformly
            return dt.replace(tzinfo=None)
        # Legacy SQLite format
        return datetime.strptime(str(dt_str), '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None


# ─── Ghost-session guard ──────────────────────────────────────────────────────

@app.before_request
def validate_session_user():
    """Clear the session if the logged-in user no longer exists in the DB."""
    user_id = session.get('user_id')
    if user_id and db.get_user_by_id(user_id) is None:
        session.clear()
        flash('Your account no longer exists. Please register or log in again.', 'warning')
        return redirect(url_for('login'))


# ─── Auth decorators ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Admin auth via ADMIN_EMAIL / ADMIN_PASSWORD stored in .env."""
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_email = os.getenv('ADMIN_EMAIL', '')
        admin_password = os.getenv('ADMIN_PASSWORD', '')

        if not admin_password:
            return 'Admin not configured.', 403

        # Check session-based admin login
        if session.get('is_admin'):
            return f(*args, **kwargs)

        # Check Basic Auth header (for API/programmatic access)
        import base64
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Basic '):
            try:
                credentials = base64.b64decode(auth[6:]).decode('utf-8')
                username, password = credentials.split(':', 1)
                if username == admin_email and password == admin_password:
                    return f(*args, **kwargs)
            except Exception:
                pass

        return redirect(url_for('admin_login'))
    return decorated


# ─── API helper ───────────────────────────────────────────────────────────────

def get_exercises_from_api(muscle='', ex_type='', difficulty='', name=''):
    """Call API Ninjas and return a list of exercises or an error string."""
    params = {}
    if muscle:
        params['muscle'] = muscle
    if ex_type:
        params['type'] = ex_type
    if difficulty:
        params['difficulty'] = difficulty
    if name:
        params['name'] = name

    try:
        resp = requests.get(
            API_URL,
            headers={'X-Api-Key': API_KEY},
            params=params,
            timeout=8
        )
        if resp.status_code == 200:
            return resp.json(), None
        return [], f'API error {resp.status_code}'
    except requests.Timeout:
        return [], 'Request timed out. Please try again.'
    except requests.ConnectionError:
        return [], 'Could not reach the exercise database. Check your internet connection.'


# ─── Health calculations ──────────────────────────────────────────────────────

def calculate_bmi(weight, height):
    if not weight or not height or height == 0:
        return None, None
    bmi = round(weight / ((height / 100) ** 2), 1)
    if bmi < 18.5:
        category = 'Underweight'
    elif bmi < 25:
        category = 'Normal'
    elif bmi < 30:
        category = 'Overweight'
    else:
        category = 'Obese'
    return bmi, category


def calculate_bmr(weight, height, age, gender):
    if not all([weight, height, age, gender]):
        return None
    if gender.lower() == 'male':
        return round(10 * weight + 6.25 * height - 5 * age + 5)
    else:
        return round(10 * weight + 6.25 * height - 5 * age - 161)


# ─── Sitemap ──────────────────────────────────────────────────────────────────

@app.route('/sitemap.xml')
def sitemap():
    base = 'https://exercise-finder.vercel.app'
    pages = [
        ('/', '1.0', 'weekly'),
        ('/login', '0.8', 'monthly'),
        ('/register', '0.8', 'monthly'),
        ('/calculator', '0.7', 'monthly'),
    ]
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority, freq in pages:
        xml_parts.append(f'''  <url>
    <loc>{base}{path}</loc>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>''')
    xml_parts.append('</urlset>')
    return Response('\n'.join(xml_parts), mimetype='application/xml')


# ─── Landing ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/google9f453f9a2cf3553a.html')
def google_verify():
    return send_from_directory(app.static_folder, 'google9f453f9a2cf3553a.html')


# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        import re
        if len(username) < 3 or len(username) > 20 or not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores.', 'error')
            return render_template('auth/register.html')

        if len(password) < 5 or \
           not re.search(r'[A-Z]', password) or \
           not re.search(r'[a-z]', password) or \
           not re.search(r'\d', password) or \
           not re.search(r'[^A-Za-z0-9]', password):
            flash('Password must be at least 5 characters, with upper, lower, number, and special character.', 'error')
            return render_template('auth/register.html')

        if db.get_user_by_email(email):
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')

        hashed = generate_password_hash(password)
        db.create_user(username, email, hashed)

        user = db.get_user_by_email(email)
        session['user_id'] = user['id']
        session['username'] = user['username']

        flash('Account created! Welcome to your dashboard.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember_me') == 'on'

        user = db.get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session.permanent = remember
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── Profile ──────────────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db.get_user_by_id(session['user_id'])
    if request.method == 'POST':
        username = request.form.get('username', '').strip()

        import re
        if len(username) < 3 or len(username) > 20 or not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores.', 'error')
            return render_template('profile.html', user=user)

        try:
            age = int(request.form.get('age', 0))
            height = float(request.form.get('height', 0))
            weight = float(request.form.get('weight', 0))
        except ValueError:
            flash('Please enter valid numeric values for age, height, and weight.', 'error')
            return render_template('profile.html', user=user)

        gender = request.form.get('gender', '')

        if age <= 0 or height <= 0 or weight <= 0:
            flash('Age, height, and weight must be positive numbers.', 'error')
            return render_template('profile.html', user=user)

        db.update_profile(session['user_id'], username, age, height, weight, gender)
        session['username'] = username
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.get_user_by_id(session['user_id'])
    bmi, bmi_category = calculate_bmi(user['weight'], user['height'])
    bmr = calculate_bmr(user['weight'], user['height'], user['age'], user['gender'])
    stats = db.get_progress_stats(session['user_id'])
    goals = db.get_goals(session['user_id'])
    plans = db.get_workout_plans(session['user_id'])

    at_risk = bmi_category in ('Obese',) or (bmi is not None and bmi < 16)

    return render_template('dashboard.html',
                           user=user, bmi=bmi, bmi_category=bmi_category,
                           bmr=bmr, stats=stats, goals=goals, at_risk=at_risk,
                           plans=plans)


# ─── Health Calculator ────────────────────────────────────────────────────────

@app.route('/calculator', methods=['GET', 'POST'])
@login_required
def calculator():
    result = None
    form_data = {}

    if request.method == 'POST':
        try:
            weight = float(request.form.get('weight', 0))
            height = float(request.form.get('height', 0))
            age    = int(request.form.get('age', 0))
            gender = request.form.get('gender', '')

            form_data = {'weight': weight, 'height': height, 'age': age, 'gender': gender}

            if weight <= 0 or height <= 0 or age <= 0 or not gender:
                flash('Please fill in all fields with valid positive values.', 'error')
            else:
                bmi, bmi_category = calculate_bmi(weight, height)
                bmr = calculate_bmr(weight, height, age, gender)
                at_risk = bmi_category in ('Obese',) or (bmi is not None and bmi < 16)
                result = {
                    'bmi': bmi,
                    'bmi_category': bmi_category,
                    'bmr': bmr,
                    'at_risk': at_risk,
                    'weight': weight,
                    'height': height,
                    'age': age,
                    'gender': gender,
                }
        except ValueError:
            flash('Please enter valid numeric values.', 'error')

    return render_template('calculator.html', result=result, form_data=form_data)


@app.route('/calculator/save-to-profile', methods=['POST'])
@login_required
def save_calculator_to_profile():
    try:
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))
        age    = int(request.form.get('age', 0))
        gender = request.form.get('gender', '')

        if weight <= 0 or height <= 0 or age <= 0 or not gender:
            flash('Invalid data — profile not updated.', 'error')
            return redirect(url_for('calculator'))

        user = db.get_user_by_id(session['user_id'])
        db.update_profile(session['user_id'], user['username'], age, height, weight, gender)
        flash('✅ Your profile has been updated with these measurements!', 'success')
    except ValueError:
        flash('Invalid data — profile not updated.', 'error')

    return redirect(url_for('calculator'))


# ─── Exercise Search ──────────────────────────────────────────────────────────

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    exercises = []
    error = None
    muscle = ex_type = difficulty = name = ''
    limit = 10
    fav_names = {f['exercise_name'] for f in db.get_favourites(session['user_id'])}

    if request.method == 'POST':
        muscle = request.form.get('muscle', '').strip()
        ex_type = request.form.get('type', '')
        difficulty = request.form.get('difficulty', '')
        name = request.form.get('name', '').strip()
        try:
            limit = int(request.form.get('limit', 10))
            if limit not in (5, 10, 15, 20, 30):
                limit = 10
        except ValueError:
            limit = 10
        all_exercises, error = get_exercises_from_api(muscle, ex_type, difficulty, name)
        exercises = all_exercises[:limit]

    return render_template('search.html',
                           exercises=exercises, error=error,
                           muscle=muscle, ex_type=ex_type, name=name,
                           difficulty=difficulty, fav_names=fav_names, limit=limit)


# ─── Muscle Map API ───────────────────────────────────────────────────────────

@app.route('/api/muscle-exercises')
@login_required
def muscle_exercises_api():
    """Return exercises for a given muscle as JSON (used by muscle map UI)."""
    muscle = request.args.get('muscle', '').strip()
    if not muscle:
        return jsonify({'exercises': [], 'error': 'No muscle specified'})
    exercises, error = get_exercises_from_api(muscle=muscle)
    fav_names = {f['exercise_name'] for f in db.get_favourites(session['user_id'])}
    for ex in exercises:
        ex['is_favourite'] = ex.get('name', '') in fav_names
    return jsonify({'exercises': exercises[:10], 'error': error})


# ─── Add Workout ──────────────────────────────────────────────────────────────

@app.route('/add-workout', methods=['GET', 'POST'])
@login_required
def add_workout():
    if request.method == 'POST':
        activity = request.form.get('activity', '').strip()
        try:
            duration = int(request.form.get('duration', 0))
            cal_raw = request.form.get('calories', '').strip()
            calories = int(cal_raw) if cal_raw else 0
            sets = int(request.form.get('sets', 0) or 0)
            reps = int(request.form.get('reps', 0) or 0)
        except ValueError:
            flash('Duration, sets, and reps must be whole numbers.', 'error')
            return render_template('add_workout.html')

        if not activity or duration <= 0:
            flash('Activity name and duration are required.', 'error')
            return render_template('add_workout.html')

        db.add_history(session['user_id'], activity, duration, calories, sets, reps)
        flash('Workout saved to Timeline!', 'success')
        return redirect(url_for('timeline'))

    return render_template('add_workout.html')


# ─── Timeline ─────────────────────────────────────────────────────────────────

@app.route('/timeline')
@login_required
def timeline():
    query = request.args.get('q', '')
    history = db.get_history(session['user_id'], query if query else None)
    return render_template('timeline.html', history=history, query=query)


@app.route('/timeline/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_history_item(item_id):
    db.delete_history_item(session['user_id'], item_id)
    flash('Workout entry deleted.', 'info')
    return redirect(url_for('timeline'))


# ─── Progress ─────────────────────────────────────────────────────────────────

@app.route('/progress')
@login_required
def progress():
    stats = db.get_progress_stats(session['user_id'])
    weight_log = db.get_weight_log(session['user_id'])
    labels = [str(row['logged_at'])[:10] for row in weight_log]
    weights = [row['weight'] for row in weight_log]
    return render_template('progress.html', stats=stats,
                           weight_labels=labels, weight_data=weights)


# ─── Goals ────────────────────────────────────────────────────────────────────

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    if request.method == 'POST':
        recent = db.get_recent_goal(session['user_id'])
        if recent:
            set_at = parse_datetime(recent['set_at'])
            if set_at and datetime.now() - set_at < timedelta(hours=24):
                flash('Goals cannot be modified within 24 hours of the last change.', 'warning')
                return redirect(url_for('goals'))

        category = request.form.get('category', '')
        target_date = request.form.get('target_date', '')
        try:
            target_value = float(request.form.get('target_value', 0))
        except ValueError:
            flash('Please enter a valid goal value.', 'error')
            return redirect(url_for('goals'))

        if not category or not target_date or target_value <= 0:
            flash('Please enter valid goal details.', 'error')
            return redirect(url_for('goals'))

        db.add_goal(session['user_id'], category, target_value, target_date)
        flash('Goal saved!', 'success')
        return redirect(url_for('goals'))

    user_goals = db.get_goals(session['user_id'])
    user = db.get_user_by_id(session['user_id'])

    goals_with_eta = []
    for g in user_goals:
        eta = None
        progress_pct = 0
        current_val = None

        if g['category'] == 'Weight Target' and user['weight']:
            current_val = user['weight']
            diff = abs(current_val - g['target_value'])
            weeks_needed = diff / 0.75
            eta = (datetime.now() + timedelta(weeks=weeks_needed)).strftime('%Y-%m-%d')
            if diff > 0:
                start_diff = diff + 1
                progress_pct = max(0, min(100, int((1 - diff / start_diff) * 100)))

        goals_with_eta.append({
            'goal': g,
            'eta': eta,
            'progress_pct': progress_pct,
            'current_val': current_val
        })

    recent = db.get_recent_goal(session['user_id'])
    can_set_goal = True
    hours_left = 0
    if recent:
        set_at = parse_datetime(recent['set_at'])
        if set_at:
            diff = datetime.now() - set_at
            if diff < timedelta(hours=24):
                can_set_goal = False
                hours_left = round((timedelta(hours=24) - diff).seconds / 3600, 1)

    return render_template('goals.html',
                           goals_with_eta=goals_with_eta,
                           can_set_goal=can_set_goal,
                           hours_left=hours_left)


@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    db.delete_goal(session['user_id'], goal_id)
    flash('Goal deleted.', 'info')
    return redirect(url_for('goals'))


# ─── Favourites ───────────────────────────────────────────────────────────────

@app.route('/favourites')
@login_required
def favourites():
    favs = db.get_favourites(session['user_id'])
    return render_template('favourites.html', favourites=favs)


@app.route('/favourite/add', methods=['POST'])
@login_required
def add_favourite():
    data = request.get_json()
    added = db.add_favourite(
        session['user_id'],
        data.get('name', ''),
        data.get('type', ''),
        data.get('muscle', ''),
        data.get('difficulty', ''),
        data.get('instructions', '')
    )
    return jsonify({'success': added, 'message': 'Added to Favourites' if added else 'Already in Favourites'})


@app.route('/favourite/remove', methods=['POST'])
@login_required
def remove_favourite():
    data = request.get_json()
    db.remove_favourite(session['user_id'], data.get('name', ''))
    return jsonify({'success': True, 'message': 'Removed from Favourites'})


# ─── Workout Plans & Checklist ────────────────────────────────────────────────

@app.route('/plans')
@login_required
def plans():
    """List all workout plans for the user."""
    user_plans = db.get_workout_plans(session['user_id'])
    return render_template('plans.html', plans=user_plans)


@app.route('/plans/<int:plan_id>')
@login_required
def view_plan(plan_id):
    """View and use a specific workout plan as a checklist."""
    plan = db.get_workout_plan(plan_id, session['user_id'])
    if not plan:
        flash('Plan not found.', 'error')
        return redirect(url_for('plans'))
    return render_template('plan_detail.html', plan=plan)


@app.route('/plans/<int:plan_id>/save-progress', methods=['POST'])
@login_required
def save_plan_progress(plan_id):
    """Save checklist state (checked exercises) back to the plan."""
    data = request.get_json()
    exercises = data.get('exercises', [])
    db.update_workout_plan_exercises(plan_id, session['user_id'], exercises)
    return jsonify({'success': True})


@app.route('/plans/<int:plan_id>/complete', methods=['POST'])
@login_required
def complete_plan(plan_id):
    """Log all completed exercises from a plan to history."""
    plan = db.get_workout_plan(plan_id, session['user_id'])
    if not plan:
        return jsonify({'success': False, 'message': 'Plan not found'})

    exercises = plan.get('exercises', [])
    if isinstance(exercises, str):
        exercises = json.loads(exercises)

    logged = 0
    for ex in exercises:
        if ex.get('completed'):
            db.add_history(
                session['user_id'],
                ex.get('name', 'Exercise'),
                ex.get('duration', 0),
                ex.get('calories', 0),
                ex.get('sets', 0),
                ex.get('reps', 0)
            )
            logged += 1

    return jsonify({'success': True, 'logged': logged})


@app.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    db.delete_workout_plan(plan_id, session['user_id'])
    flash('Plan deleted.', 'info')
    return redirect(url_for('plans'))


@app.route('/plans/create', methods=['GET', 'POST'])
@login_required
def create_plan():
    """Manually create a workout plan."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        exercises_json = request.form.get('exercises', '[]')
        try:
            exercises = json.loads(exercises_json)
        except Exception:
            exercises = []

        if not name:
            flash('Plan name is required.', 'error')
            return render_template('create_plan.html')

        db.add_workout_plan(session['user_id'], name, description, exercises, ai_generated=False)
        flash('Workout plan created!', 'success')
        return redirect(url_for('plans'))

    return render_template('create_plan.html')


# ─── AI Workout Recommendations ───────────────────────────────────────────────

# Fallback templates used when Gemini key is not configured
WORKOUT_TEMPLATES = {
    'strength': {
        'name': 'Strength Builder',
        'description': 'Classic 5x5 strength program',
        'exercises': [
            {'name': 'Barbell Squat', 'sets': 5, 'reps': 5, 'duration': 15, 'calories': 80, 'muscle': 'quadriceps', 'completed': False},
            {'name': 'Bench Press', 'sets': 5, 'reps': 5, 'duration': 12, 'calories': 60, 'muscle': 'chest', 'completed': False},
            {'name': 'Deadlift', 'sets': 1, 'reps': 5, 'duration': 10, 'calories': 70, 'muscle': 'lower_back', 'completed': False},
            {'name': 'Overhead Press', 'sets': 5, 'reps': 5, 'duration': 10, 'calories': 50, 'muscle': 'shoulders', 'completed': False},
            {'name': 'Barbell Row', 'sets': 5, 'reps': 5, 'duration': 10, 'calories': 55, 'muscle': 'middle_back', 'completed': False},
        ]
    },
    'hypertrophy': {
        'name': 'Muscle Builder (PPL)',
        'description': 'Push Pull Legs hypertrophy split',
        'exercises': [
            {'name': 'Incline Dumbbell Press', 'sets': 4, 'reps': 10, 'duration': 12, 'calories': 60, 'muscle': 'chest', 'completed': False},
            {'name': 'Cable Fly', 'sets': 3, 'reps': 12, 'duration': 8, 'calories': 40, 'muscle': 'chest', 'completed': False},
            {'name': 'Lateral Raises', 'sets': 4, 'reps': 15, 'duration': 8, 'calories': 35, 'muscle': 'shoulders', 'completed': False},
            {'name': 'Tricep Pushdown', 'sets': 3, 'reps': 12, 'duration': 8, 'calories': 35, 'muscle': 'triceps', 'completed': False},
            {'name': 'Overhead Tricep Extension', 'sets': 3, 'reps': 12, 'duration': 8, 'calories': 30, 'muscle': 'triceps', 'completed': False},
        ]
    },
    'fat_loss': {
        'name': 'Fat Burn Circuit',
        'description': 'High-intensity circuit for calorie burn',
        'exercises': [
            {'name': 'Burpees', 'sets': 4, 'reps': 15, 'duration': 10, 'calories': 100, 'muscle': 'abdominals', 'completed': False},
            {'name': 'Jump Squats', 'sets': 4, 'reps': 20, 'duration': 8, 'calories': 80, 'muscle': 'quadriceps', 'completed': False},
            {'name': 'Mountain Climbers', 'sets': 3, 'reps': 30, 'duration': 8, 'calories': 70, 'muscle': 'abdominals', 'completed': False},
            {'name': 'Push-Ups', 'sets': 3, 'reps': 20, 'duration': 6, 'calories': 50, 'muscle': 'chest', 'completed': False},
            {'name': 'High Knees', 'sets': 4, 'reps': 40, 'duration': 6, 'calories': 60, 'muscle': 'quadriceps', 'completed': False},
        ]
    },
    'home': {
        'name': 'Home Workout (No Equipment)',
        'description': 'Effective bodyweight routine for home',
        'exercises': [
            {'name': 'Push-Ups', 'sets': 4, 'reps': 15, 'duration': 8, 'calories': 45, 'muscle': 'chest', 'completed': False},
            {'name': 'Bodyweight Squats', 'sets': 4, 'reps': 20, 'duration': 8, 'calories': 55, 'muscle': 'quadriceps', 'completed': False},
            {'name': 'Plank', 'sets': 3, 'reps': 1, 'duration': 5, 'calories': 20, 'muscle': 'abdominals', 'completed': False},
            {'name': 'Glute Bridge', 'sets': 3, 'reps': 20, 'duration': 6, 'calories': 30, 'muscle': 'glutes', 'completed': False},
            {'name': 'Tricep Dips (Chair)', 'sets': 3, 'reps': 12, 'duration': 6, 'calories': 30, 'muscle': 'triceps', 'completed': False},
        ]
    },
    'cardio': {
        'name': 'Cardio Endurance',
        'description': 'Steady-state and interval cardio mix',
        'exercises': [
            {'name': 'Treadmill Run', 'sets': 1, 'reps': 1, 'duration': 20, 'calories': 180, 'muscle': 'quadriceps', 'completed': False},
            {'name': 'Cycling (Stationary)', 'sets': 1, 'reps': 1, 'duration': 15, 'calories': 130, 'muscle': 'quadriceps', 'completed': False},
            {'name': 'Jump Rope', 'sets': 5, 'reps': 1, 'duration': 3, 'calories': 50, 'muscle': 'calves', 'completed': False},
            {'name': 'Rowing Machine', 'sets': 1, 'reps': 1, 'duration': 10, 'calories': 100, 'muscle': 'middle_back', 'completed': False},
        ]
    }
}


def generate_ai_plan(user_goal, user, fitness_level='beginner'):
    """Generate workout plan via Gemini API or fall back to templates."""
    if not GEMINI_API_KEY:
        return None, 'no_key'

    prompt = f"""You are a certified personal trainer. Create a detailed workout plan in JSON format.

User Profile:
- Goal: {user_goal}
- Fitness Level: {fitness_level}
- Age: {user.get('age', 'unknown')}
- Weight: {user.get('weight', 'unknown')} kg
- Gender: {user.get('gender', 'unknown')}

Return ONLY a valid JSON object in this exact format (no markdown, no extra text):
{{
  "name": "Plan Name",
  "description": "Brief description",
  "exercises": [
    {{
      "name": "Exercise Name",
      "sets": 3,
      "reps": 12,
      "duration": 10,
      "calories": 50,
      "muscle": "muscle_group",
      "instructions": "Brief form instructions",
      "completed": false
    }}
  ]
}}

Include 5-7 exercises. Duration is in minutes per set. Make it realistic for the user's level."""

    try:
        resp = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}',
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 1024}
            },
            timeout=15
        )
        if resp.status_code == 200:
            raw = resp.json()['candidates'][0]['content']['parts'][0]['text']
            # Strip markdown code fences if present
            raw = raw.strip().lstrip('```json').lstrip('```').rstrip('```').strip()
            plan_data = json.loads(raw)
            return plan_data, None
        return None, f'API error {resp.status_code}'
    except Exception as e:
        return None, str(e)


@app.route('/ai-plan', methods=['GET', 'POST'])
@login_required
def ai_plan():
    """AI Workout Recommendation page."""
    user = db.get_user_by_id(session['user_id'])
    ai_available = bool(GEMINI_API_KEY)
    generated_plan = None
    error = None

    if request.method == 'POST':
        action = request.form.get('action', 'generate')

        if action == 'save' and request.form.get('plan_json'):
            try:
                plan_data = json.loads(request.form.get('plan_json'))
                ai_generated = request.form.get('ai_generated') == 'true'
                db.add_workout_plan(
                    session['user_id'],
                    plan_data['name'],
                    plan_data.get('description', ''),
                    plan_data['exercises'],
                    ai_generated=ai_generated
                )
                flash('Workout plan saved! Head to Plans to start your checklist.', 'success')
                return redirect(url_for('plans'))
            except Exception as e:
                flash(f'Could not save plan: {e}', 'error')
                return redirect(url_for('ai_plan'))

        # Generate action
        user_goal = request.form.get('goal', '').strip()
        fitness_level = request.form.get('fitness_level', 'beginner')
        template_type = request.form.get('template_type', '')

        if not user_goal and not template_type:
            flash('Please describe your goal or pick a template.', 'error')
            return render_template('ai_plan.html', user=user, ai_available=ai_available)

        if template_type and template_type in WORKOUT_TEMPLATES:
            # Use a template
            generated_plan = WORKOUT_TEMPLATES[template_type].copy()
            generated_plan['ai_generated'] = False
        elif ai_available:
            generated_plan, error = generate_ai_plan(user_goal, user, fitness_level)
            if generated_plan:
                generated_plan['ai_generated'] = True
            else:
                # Fall back to closest template
                if 'strength' in user_goal.lower() or 'muscle' in user_goal.lower():
                    generated_plan = WORKOUT_TEMPLATES['strength'].copy()
                elif 'fat' in user_goal.lower() or 'weight loss' in user_goal.lower():
                    generated_plan = WORKOUT_TEMPLATES['fat_loss'].copy()
                elif 'home' in user_goal.lower():
                    generated_plan = WORKOUT_TEMPLATES['home'].copy()
                else:
                    generated_plan = WORKOUT_TEMPLATES['hypertrophy'].copy()
                generated_plan['ai_generated'] = False
                flash(f'AI unavailable ({error}). Showing template instead.', 'warning')
        else:
            # No API key — use template based on goal keywords
            if 'strength' in user_goal.lower() or 'strong' in user_goal.lower():
                generated_plan = WORKOUT_TEMPLATES['strength'].copy()
            elif 'fat' in user_goal.lower() or 'lose weight' in user_goal.lower() or 'cut' in user_goal.lower():
                generated_plan = WORKOUT_TEMPLATES['fat_loss'].copy()
            elif 'home' in user_goal.lower() or 'no equipment' in user_goal.lower():
                generated_plan = WORKOUT_TEMPLATES['home'].copy()
            elif 'cardio' in user_goal.lower() or 'endurance' in user_goal.lower():
                generated_plan = WORKOUT_TEMPLATES['cardio'].copy()
            else:
                generated_plan = WORKOUT_TEMPLATES['hypertrophy'].copy()
            generated_plan['ai_generated'] = False

    return render_template('ai_plan.html', user=user, ai_available=ai_available,
                           generated_plan=generated_plan, error=error,
                           templates=WORKOUT_TEMPLATES)


# ─── Muscle Map ───────────────────────────────────────────────────────────────

@app.route('/muscle-map')
@login_required
def muscle_map():
    """Interactive muscle map page."""
    return render_template('muscle_map.html')


# ─── Admin: Login ─────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('view_database'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        admin_email = os.getenv('ADMIN_EMAIL', '')
        admin_password = os.getenv('ADMIN_PASSWORD', '')

        if email == admin_email and password == admin_password:
            session['is_admin'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('view_database'))
        flash('Invalid admin credentials.', 'error')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin session ended.', 'info')
    return redirect(url_for('admin_login'))


# ─── Admin: DB Viewer ─────────────────────────────────────────────────────────

@app.route('/admin/db')
@admin_required
def view_database():
    db_data = db.get_all_table_data()
    return render_template('admin_db.html', db_data=db_data)


@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_view_user(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('view_database'))

    history = db.get_history(user_id)
    weight_log = db.get_weight_log(user_id)
    goals = db.get_goals(user_id)
    favs = db.get_favourites(user_id)

    return render_template('admin_user_details.html', user=user, history=history,
                           weight_log=weight_log, goals=goals, favs=favs)


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    db.delete_user(user_id)
    if session.get('user_id') == user_id:
        session.clear()
    flash(f'User #{user_id} and all related data permanently deleted.', 'success')
    return redirect(url_for('view_database'))


# ═══════════════════════════════════════════════════════════════════════════════
# ─── MOBILE REST API  (/api/mobile/*)  ─────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def _cors(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-User-Id'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.after_request
def add_cors(response):
    return _cors(response)

@app.route('/api/mobile/<path:p>', methods=['OPTIONS'])
def mobile_preflight(p):
    return _cors(jsonify({}))


def mobile_auth_required(f):
    """Check X-User-Id header for mobile API requests."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id_str = request.headers.get('X-User-Id')
        if not user_id_str:
            return jsonify({'error': 'Unauthorised — missing X-User-Id header'}), 401
        try:
            uid = int(user_id_str)
        except ValueError:
            return jsonify({'error': 'Invalid user id'}), 401
        user = db.get_user_by_id(uid)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        request.mobile_user = user
        request.mobile_user_id = uid
        return f(*args, **kwargs)
    return decorated


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/api/mobile/auth/register', methods=['POST'])
def mobile_register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not all([username, email, password]):
        return jsonify({'error': 'username, email and password are required'}), 400
    if db.get_user_by_email(email):
        return jsonify({'error': 'Email already registered'}), 409

    pw_hash = generate_password_hash(password)
    user_id = db.create_user(username, email, pw_hash)
    return jsonify({'success': True, 'user_id': user_id, 'username': username}), 201


@app.route('/api/mobile/auth/login', methods=['POST'])
def mobile_login():
    data = request.get_json(silent=True) or {}
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '').strip()

    user = db.get_user_by_email(email)
    if not user or not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({'error': 'Invalid email or password'}), 401

    return jsonify({
        'success':  True,
        'user_id':  user['id'],
        'username': user['username'],
        'email':    user['email'],
    })


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/api/mobile/dashboard')
@mobile_auth_required
def mobile_dashboard():
    user    = request.mobile_user
    uid     = request.mobile_user_id
    history = db.get_history(uid) or []
    wlog    = db.get_weight_log(uid) or []

    # Stats
    total_workouts  = len(history)
    total_calories  = sum(int(h.get('calories', 0) or 0) for h in history)
    total_minutes   = sum(int(h.get('duration', 0) or 0) for h in history)
    latest_weight   = wlog[-1]['weight'] if wlog else None

    # BMI / BMR
    age    = user.get('age')
    height = user.get('height')
    weight = user.get('weight') or (latest_weight)
    gender = user.get('gender', 'male')
    bmi = bmr = None
    if height and weight:
        h_m = float(height) / 100
        bmi = round(float(weight) / (h_m * h_m), 1)
    if age and height and weight:
        if gender == 'male':
            bmr = round(10*float(weight) + 6.25*float(height) - 5*float(age) + 5)
        else:
            bmr = round(10*float(weight) + 6.25*float(height) - 5*float(age) - 161)

    # Recent activity (last 5)
    recent = []
    for h in sorted(history, key=lambda x: x.get('date',''), reverse=True)[:5]:
        recent.append({
            'id':        h.get('id'),
            'exercise':  h.get('exercise_name'),
            'date':      h.get('date'),
            'sets':      h.get('sets'),
            'reps':      h.get('reps'),
            'duration':  h.get('duration'),
            'calories':  h.get('calories'),
            'muscle':    h.get('muscle_group'),
        })

    return jsonify({
        'user':            {'id': uid, 'username': user.get('username'), 'email': user.get('email')},
        'stats':           {'workouts': total_workouts, 'calories': total_calories, 'minutes': total_minutes},
        'bmi':             bmi,
        'bmr':             bmr,
        'latest_weight':   latest_weight,
        'recent_activity': recent,
    })


# ── Search ────────────────────────────────────────────────────────────────────

@app.route('/api/mobile/search')
@mobile_auth_required
def mobile_search():
    muscle     = request.args.get('muscle', '')
    ex_type    = request.args.get('type', '')
    difficulty = request.args.get('difficulty', '')
    name       = request.args.get('name', '')

    exercises = get_exercises_from_api(muscle, ex_type, difficulty, name)
    if isinstance(exercises, str):
        return jsonify({'error': exercises, 'exercises': []}), 200

    uid  = request.mobile_user_id
    favs = {f['exercise_name'] for f in (db.get_favourites(uid) or [])}
    for ex in exercises:
        ex['is_favourite'] = ex.get('name') in favs

    return jsonify({'exercises': exercises})


# ── Muscle map exercises ───────────────────────────────────────────────────────

@app.route('/api/mobile/muscle-exercises')
@mobile_auth_required
def mobile_muscle_exercises():
    muscle    = request.args.get('muscle', '')
    exercises = get_exercises_from_api(muscle=muscle)
    if isinstance(exercises, str):
        return jsonify({'exercises': []}), 200

    uid  = request.mobile_user_id
    favs = {f['exercise_name'] for f in (db.get_favourites(uid) or [])}
    for ex in exercises:
        ex['is_favourite'] = ex.get('name') in favs

    return jsonify({'exercises': exercises, 'muscle': muscle})


# ── Workout history / timeline ────────────────────────────────────────────────

@app.route('/api/mobile/timeline')
@mobile_auth_required
def mobile_timeline():
    uid     = request.mobile_user_id
    history = db.get_history(uid) or []
    history.sort(key=lambda x: x.get('date', ''), reverse=True)
    return jsonify({'history': history})


@app.route('/api/mobile/workout', methods=['POST'])
@mobile_auth_required
def mobile_add_workout():
    data = request.get_json(silent=True) or {}
    uid  = request.mobile_user_id
    db.add_history(
        user_id=uid,
        activity=data.get('exercise_name', ''),
        sets=data.get('sets', 3),
        reps=data.get('reps', 10),
        duration=data.get('duration', 30),
        calories=data.get('calories', 100),
    )
    return jsonify({'success': True})


@app.route('/api/mobile/workout/<int:entry_id>', methods=['DELETE'])
@mobile_auth_required
def mobile_delete_workout(entry_id):
    uid = request.mobile_user_id
    db.delete_history_item(uid, entry_id)
    return jsonify({'success': True})


# ── Progress ──────────────────────────────────────────────────────────────────

@app.route('/api/mobile/progress')
@mobile_auth_required
def mobile_progress():
    uid     = request.mobile_user_id
    history = db.get_history(uid) or []
    wlog    = db.get_weight_log(uid) or []

    total_workouts = len(history)
    total_calories = sum(int(h.get('calories', 0) or 0) for h in history)
    total_minutes  = sum(int(h.get('duration', 0) or 0) for h in history)

    # Most worked muscle
    muscles = [h.get('muscle_group') for h in history if h.get('muscle_group')]
    from collections import Counter
    top_muscle = Counter(muscles).most_common(1)[0][0] if muscles else None

    # Weight trend
    weight_trend = [{'date': w['date'], 'weight': w['weight']} for w in wlog[-30:]]

    # Weekly frequency (last 8 weeks)
    weekly = {}
    for h in history:
        dt = parse_datetime(h.get('date'))
        if dt:
            week_label = dt.strftime('%Y-W%U')
            weekly[week_label] = weekly.get(week_label, 0) + 1

    return jsonify({
        'stats': {
            'total_workouts': total_workouts,
            'total_calories': total_calories,
            'total_minutes':  total_minutes,
            'top_muscle':     top_muscle,
        },
        'weight_trend':    weight_trend,
        'weekly_frequency': weekly,
    })


# ── Goals ─────────────────────────────────────────────────────────────────────

@app.route('/api/mobile/goals', methods=['GET'])
@mobile_auth_required
def mobile_get_goals():
    uid   = request.mobile_user_id
    goals = db.get_goals(uid) or []
    return jsonify({'goals': goals})


@app.route('/api/mobile/goals', methods=['POST'])
@mobile_auth_required
def mobile_add_goal():
    data = request.get_json(silent=True) or {}
    uid  = request.mobile_user_id
    db.add_goal(
        user_id=uid,
        goal_type=data.get('goal_type', ''),
        target_value=data.get('target_value', 0),
        current_value=data.get('current_value', 0),
        target_date=data.get('target_date'),
        description=data.get('description', ''),
    )
    return jsonify({'success': True}), 201


@app.route('/api/mobile/goals/<int:goal_id>', methods=['PUT'])
@mobile_auth_required
def mobile_update_goal(goal_id):
    data = request.get_json(silent=True) or {}
    uid  = request.mobile_user_id
    db.update_goal(uid, goal_id, data.get('current_value'))
    return jsonify({'success': True})


@app.route('/api/mobile/goals/<int:goal_id>', methods=['DELETE'])
@mobile_auth_required
def mobile_delete_goal(goal_id):
    uid = request.mobile_user_id
    db.delete_goal(uid, goal_id)
    return jsonify({'success': True})


# ── Favourites ────────────────────────────────────────────────────────────────

@app.route('/api/mobile/favourites', methods=['GET'])
@mobile_auth_required
def mobile_get_favourites():
    uid  = request.mobile_user_id
    favs = db.get_favourites(uid) or []
    return jsonify({'favourites': favs})


@app.route('/api/mobile/favourites', methods=['POST'])
@mobile_auth_required
def mobile_add_favourite():
    data = request.get_json(silent=True) or {}
    uid  = request.mobile_user_id
    db.add_favourite(
        user_id=uid,
        exercise_name=data.get('name', ''),
        exercise_type=data.get('type', ''),
        muscle=data.get('muscle', ''),
        difficulty=data.get('difficulty', ''),
        instructions=data.get('instructions', ''),
    )
    return jsonify({'success': True})


@app.route('/api/mobile/favourites/<int:fav_id>', methods=['DELETE'])
@mobile_auth_required
def mobile_remove_favourite(fav_id):
    uid = request.mobile_user_id
    db.remove_favourite(uid, fav_id)
    return jsonify({'success': True})


# ── Workout Plans (mobile) ────────────────────────────────────────────────────

@app.route('/api/mobile/plans', methods=['GET'])
@mobile_auth_required
def mobile_get_plans():
    uid   = request.mobile_user_id
    plans = db.get_plans(uid) or []
    return jsonify({'plans': plans})


@app.route('/api/mobile/plans', methods=['POST'])
@mobile_auth_required
def mobile_create_plan():
    data      = request.get_json(silent=True) or {}
    uid       = request.mobile_user_id
    plan_id   = db.create_plan(
        user_id=uid,
        name=data.get('name', 'My Plan'),
        description=data.get('description', ''),
        exercises=data.get('exercises', []),
        ai_generated=data.get('ai_generated', False),
    )
    return jsonify({'success': True, 'plan_id': plan_id}), 201


@app.route('/api/mobile/plans/<int:plan_id>', methods=['GET'])
@mobile_auth_required
def mobile_get_plan(plan_id):
    uid  = request.mobile_user_id
    plan = db.get_plan(uid, plan_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404
    return jsonify({'plan': plan})


@app.route('/api/mobile/plans/<int:plan_id>/progress', methods=['POST'])
@mobile_auth_required
def mobile_save_plan_progress(plan_id):
    data      = request.get_json(silent=True) or {}
    uid       = request.mobile_user_id
    exercises = data.get('exercises', [])
    db.update_plan_exercises(uid, plan_id, exercises)
    return jsonify({'success': True})


@app.route('/api/mobile/plans/<int:plan_id>/complete', methods=['POST'])
@mobile_auth_required
def mobile_complete_plan(plan_id):
    uid  = request.mobile_user_id
    plan = db.get_plan(uid, plan_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    logged = 0
    for ex in (plan.get('exercises') or []):
        if ex.get('completed'):
            db.add_history(
                user_id=uid,
                exercise_name=ex.get('name',''),
                sets=ex.get('sets', 3),
                reps=ex.get('reps', 10),
                weight=ex.get('weight'),
                duration=ex.get('duration', 30),
                calories=ex.get('calories', 100),
                muscle_group=ex.get('muscle', ''),
                notes=f"From plan: {plan.get('name','')}",
            )
            logged += 1
    return jsonify({'success': True, 'logged': logged})


@app.route('/api/mobile/plans/<int:plan_id>', methods=['DELETE'])
@mobile_auth_required
def mobile_delete_plan(plan_id):
    uid = request.mobile_user_id
    db.delete_plan(uid, plan_id)
    return jsonify({'success': True})


# ── Profile ───────────────────────────────────────────────────────────────────

@app.route('/api/mobile/profile', methods=['GET'])
@mobile_auth_required
def mobile_get_profile():
    user = request.mobile_user
    return jsonify({
        'id':       user.get('id'),
        'username': user.get('username'),
        'email':    user.get('email'),
        'age':      user.get('age'),
        'gender':   user.get('gender'),
        'height':   user.get('height'),
        'weight':   user.get('weight'),
    })


@app.route('/api/mobile/profile', methods=['PUT'])
@mobile_auth_required
def mobile_update_profile():
    data = request.get_json(silent=True) or {}
    uid  = request.mobile_user_id
    user = db.get_user_by_id(uid)
    db.update_profile(
        user_id=uid,
        username=user.get('username') if user else '',
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
    )
    return jsonify({'success': True})


# ── AI Plan (mobile) ──────────────────────────────────────────────────────────

@app.route('/api/mobile/ai-plan', methods=['POST'])
@mobile_auth_required
def mobile_ai_plan():
    data     = request.get_json(silent=True) or {}
    goal     = data.get('goal', 'general fitness')
    level    = data.get('fitness_level', 'intermediate')
    template = data.get('template_type', '')

    WORKOUT_TEMPLATES = {
        'strength':    {'name':'Strength Builder','exercises':[
            {'name':'Barbell Squat','sets':5,'reps':5,'muscle':'quadriceps','calories':60,'duration':5,'instructions':'Keep back straight, squat to parallel.'},
            {'name':'Deadlift','sets':4,'reps':5,'muscle':'lower_back','calories':70,'duration':5,'instructions':'Hinge at hips, neutral spine throughout.'},
            {'name':'Bench Press','sets':4,'reps':6,'muscle':'chest','calories':55,'duration':5,'instructions':'Lower bar to chest, drive up explosively.'},
            {'name':'Overhead Press','sets':3,'reps':6,'muscle':'shoulders','calories':45,'duration':4,'instructions':'Press straight overhead, core braced.'},
            {'name':'Barbell Row','sets':4,'reps':6,'muscle':'middle_back','calories':55,'duration':4,'instructions':'Hinge forward, pull bar to lower chest.'},
        ]},
        'hypertrophy': {'name':'Hypertrophy / Muscle','exercises':[
            {'name':'Incline Dumbbell Press','sets':4,'reps':12,'muscle':'chest','calories':50,'duration':4,'instructions':'Slight incline, full range of motion.'},
            {'name':'Cable Rows','sets':4,'reps':12,'muscle':'middle_back','calories':45,'duration':4,'instructions':'Squeeze scapulae at the top.'},
            {'name':'Dumbbell Lateral Raise','sets':3,'reps':15,'muscle':'shoulders','calories':35,'duration':3,'instructions':'Raise to shoulder height only.'},
            {'name':'EZ-Bar Curl','sets':3,'reps':12,'muscle':'biceps','calories':30,'duration':3,'instructions':'Keep elbows at sides.'},
            {'name':'Tricep Pushdown','sets':3,'reps':12,'muscle':'triceps','calories':30,'duration':3,'instructions':'Elbows tucked, full extension.'},
            {'name':'Leg Press','sets':4,'reps':12,'muscle':'quadriceps','calories':55,'duration':4,'instructions':'Feet shoulder-width, controlled descent.'},
        ]},
        'fat_loss': {'name':'Fat Loss HIIT','exercises':[
            {'name':'Burpees','sets':4,'reps':15,'muscle':'abdominals','calories':80,'duration':4,'instructions':'Full body explosive movement.'},
            {'name':'Kettlebell Swing','sets':4,'reps':20,'muscle':'glutes','calories':70,'duration':4,'instructions':'Hinge hips, drive hips forward powerfully.'},
            {'name':'Box Jumps','sets':3,'reps':12,'muscle':'quadriceps','calories':65,'duration':3,'instructions':'Soft landing, step down safely.'},
            {'name':'Mountain Climbers','sets':3,'reps':30,'muscle':'abdominals','calories':60,'duration':3,'instructions':'Keep hips level throughout.'},
            {'name':'Jump Rope','sets':4,'reps':60,'muscle':'calves','calories':75,'duration':4,'instructions':'Light on feet, consistent rhythm.'},
        ]},
        'home': {'name':'Home Workout (No Equipment)','exercises':[
            {'name':'Push-Ups','sets':4,'reps':20,'muscle':'chest','calories':40,'duration':4,'instructions':'Chest to floor, straight body line.'},
            {'name':'Bodyweight Squats','sets':4,'reps':25,'muscle':'quadriceps','calories':45,'duration':4,'instructions':'Knees track over toes.'},
            {'name':'Glute Bridges','sets':3,'reps':20,'muscle':'glutes','calories':35,'duration':3,'instructions':'Drive hips up, squeeze glutes at top.'},
            {'name':'Plank','sets':3,'reps':1,'muscle':'abdominals','calories':25,'duration':1,'instructions':'Hold for 45-60 seconds. Neutral spine.'},
            {'name':'Pike Push-Ups','sets':3,'reps':12,'muscle':'shoulders','calories':35,'duration':3,'instructions':'Hips high, lower head toward floor.'},
        ]},
        'cardio': {'name':'Cardio Endurance','exercises':[
            {'name':'Treadmill Run','sets':1,'reps':1,'muscle':'quadriceps','calories':200,'duration':20,'instructions':'Moderate pace, conversational effort.'},
            {'name':'Stationary Bike','sets':1,'reps':1,'muscle':'quadriceps','calories':150,'duration':15,'instructions':'80-90 RPM cadence.'},
            {'name':'Rowing Machine','sets':4,'reps':500,'muscle':'middle_back','calories':120,'duration':10,'instructions':'Drive with legs first, then lean back.'},
            {'name':'Jump Rope','sets':5,'reps':100,'muscle':'calves','calories':80,'duration':5,'instructions':'Steady rhythm, stay on toes.'},
        ]},
    }

    plan = None
    if GEMINI_API_KEY and not template:
        try:
            import requests as req
            prompt = (
                f"Create a workout plan for goal: '{goal}', fitness level: {level}. "
                "Return ONLY valid JSON in this format: "
                '{"name":"...","description":"...","exercises":['
                '{"name":"...","sets":3,"reps":10,"muscle":"...","calories":80,"duration":5,"instructions":"..."}]}'
            )
            r = req.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}",
                json={"contents":[{"parts":[{"text": prompt}]}]},
                timeout=15
            )
            if r.status_code == 200:
                text = r.json()['candidates'][0]['content']['parts'][0]['text']
                import re
                m = re.search(r'\{.*\}', text, re.DOTALL)
                if m:
                    plan = json.loads(m.group())
                    plan['ai_generated'] = True
        except Exception:
            plan = None

    if not plan:
        key = template if template in WORKOUT_TEMPLATES else list(WORKOUT_TEMPLATES.keys())[0]
        plan = WORKOUT_TEMPLATES[key].copy()
        plan['ai_generated'] = False
        plan['description'] = f"Template plan for {goal or key}"

    return jsonify({'plan': plan})


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
