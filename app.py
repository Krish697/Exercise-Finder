import os
import requests
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_from_directory)
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

import database as db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

API_KEY = os.getenv('API_NINJAS_KEY', '')
API_URL = 'https://api.api-ninjas.com/v1/exercises'

# Initialise DB on startup
db.init_db()


# ─── Ghost-session guard ──────────────────────────────────────────────────────

@app.before_request
def validate_session_user():
    """Clear the session if the logged-in user no longer exists in the DB."""
    user_id = session.get('user_id')
    if user_id and db.get_user_by_id(user_id) is None:
        session.clear()
        flash('Your account no longer exists. Please register or log in again.', 'warning')
        return redirect(url_for('login'))

# ─── Auth decorators ─────────────────────────────────────────────────────────

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: only allows the admin (set via ADMIN_EMAIL env var)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('login'))
        user = db.get_user_by_id(session['user_id'])
        if not user or not ADMIN_EMAIL or user['email'] != ADMIN_EMAIL:
            flash('Access denied. Admins only.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─── API helper ──────────────────────────────────────────────────────────────

def get_exercises_from_api(muscle='', ex_type='', difficulty=''):
    """Call API Ninjas and return a list of exercises or an error string."""
    params = {}
    if muscle:
        params['muscle'] = muscle
    if ex_type:
        params['type'] = ex_type
    if difficulty:
        params['difficulty'] = difficulty

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


# ─── Health calculations ─────────────────────────────────────────────────────

def calculate_bmi(weight, height):
    """BMI = weight(kg) / (height(m))^2"""
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
    """Mifflin-St Jeor Equation"""
    if not all([weight, height, age, gender]):
        return None
    if gender.lower() == 'male':
        return round(10 * weight + 6.25 * height - 5 * age + 5)
    else:
        return round(10 * weight + 6.25 * height - 5 * age - 161)


# ─── Landing ─────────────────────────────────────────────────────────────────

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


@app.route('/sitemap.xml')
def sitemap():
    """Generating a simple dynamic sitemap."""
    pages = []
    # Public pages
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0:
            pages.append(rule.rule)
    
    # You can add a full domain here if you know it, 
    # but search engines often handle relative paths or the provided sitemap location.
    sitemap_xml = render_template('sitemap.xml', pages=pages, now=datetime.now().strftime('%Y-%m-%d'))
    return sitemap_xml, {'Content-Type': 'application/xml'}


# ─── Auth ────────────────────────────────────────────────────────────────────

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
        
        # Automatically log in the new user
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


# ─── Profile (U3) ────────────────────────────────────────────────────────────

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


# ─── Dashboard / BMI & BMR (4.3, 4.4, U5) ───────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.get_user_by_id(session['user_id'])
    bmi, bmi_category = calculate_bmi(user['weight'], user['height'])
    bmr = calculate_bmr(user['weight'], user['height'], user['age'], user['gender'])
    stats = db.get_progress_stats(session['user_id'])
    goals = db.get_goals(session['user_id'])

    at_risk = bmi_category in ('Obese',) or (bmi is not None and bmi < 16)

    return render_template('dashboard.html',
                           user=user, bmi=bmi, bmi_category=bmi_category,
                           bmr=bmr, stats=stats, goals=goals, at_risk=at_risk)


# ─── Health Calculator (BMI & BMR) ───────────────────────────────────────────

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
    """Save calculator results to the logged-in user's profile."""
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


# ─── Workout Search (U4 / 4.5) ───────────────────────────────────────────────

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    exercises = []
    error = None
    muscle = ex_type = difficulty = ''
    limit = 10
    fav_names = {f['exercise_name'] for f in db.get_favourites(session['user_id'])}

    if request.method == 'POST':
        muscle = request.form.get('muscle', '').strip()
        ex_type = request.form.get('type', '')
        difficulty = request.form.get('difficulty', '')
        try:
            limit = int(request.form.get('limit', 10))
            if limit not in (5, 10, 15, 20, 30):
                limit = 10
        except ValueError:
            limit = 10
        all_exercises, error = get_exercises_from_api(muscle, ex_type, difficulty)
        exercises = all_exercises[:limit]

    return render_template('search.html',
                           exercises=exercises, error=error,
                           muscle=muscle, ex_type=ex_type,
                           difficulty=difficulty, fav_names=fav_names, limit=limit)


# ─── Add Workout (U6 / 4.6) ──────────────────────────────────────────────────

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


# ─── Timeline (U7 / 4.7) ─────────────────────────────────────────────────────

@app.route('/timeline')
@login_required
def timeline():
    query = request.args.get('q', '')
    history = db.get_history(session['user_id'], query if query else None)
    return render_template('timeline.html', history=history, query=query)


@app.route('/timeline/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_history_item(item_id):
    """Delete a specific workout history entry (only the owner can delete)."""
    db.delete_history_item(session['user_id'], item_id)
    flash('Workout entry deleted.', 'info')
    return redirect(url_for('timeline'))


# ─── Progress Report + Weight Graph (U8, U9 / 4.8, 4.9) ─────────────────────

@app.route('/progress')
@login_required
def progress():
    stats = db.get_progress_stats(session['user_id'])
    weight_log = db.get_weight_log(session['user_id'])
    labels = [row['logged_at'][:10] for row in weight_log]
    weights = [row['weight'] for row in weight_log]
    return render_template('progress.html', stats=stats,
                           weight_labels=labels, weight_data=weights)


# ─── Goals (U10, U11 / 4.10, 4.11) ──────────────────────────────────────────

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    if request.method == 'POST':
        # Check 24-hour lock
        recent = db.get_recent_goal(session['user_id'])
        if recent:
            set_at = datetime.strptime(recent['set_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - set_at < timedelta(hours=24):
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

    # Compute ETAs
    goals_with_eta = []
    for g in user_goals:
        eta = None
        progress_pct = 0
        current_val = None

        if g['category'] == 'Weight Target' and user['weight']:
            current_val = user['weight']
            diff = abs(current_val - g['target_value'])
            # Conservative: 0.75kg/week
            weeks_needed = diff / 0.75
            eta = (datetime.now() + timedelta(weeks=weeks_needed)).strftime('%Y-%m-%d')
            if diff > 0:
                start_diff = diff + 1  # approximate
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
        set_at = datetime.strptime(recent['set_at'], '%Y-%m-%d %H:%M:%S')
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
    """Delete a specific goal (only the owner can delete)."""
    db.delete_goal(session['user_id'], goal_id)
    flash('Goal deleted.', 'info')
    return redirect(url_for('goals'))


# ─── Favourites (U13 / 4.13) ─────────────────────────────────────────────────

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


# ─── Admin DB Viewer ────────────────────────────────────────────────────────

@app.route('/admin/db')
@admin_required
def view_database():
    """A developer tool to inspect live database contents."""
    conn = db.get_db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    
    db_data = {}
    for table in tables:
        t_name = table['name']
        # Fetching all rows; dict(row) works because of sqlite3.Row factory
        rows = conn.execute(f"SELECT * FROM {t_name}").fetchall()
        db_data[t_name] = [dict(row) for row in rows]
        
    conn.close()
    return render_template('admin_db.html', db_data=db_data)


@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_view_user(user_id):
    """View complete details for a specific user."""
    user = db.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('view_database'))
    
    history = db.get_history(user_id)
    weight_log = db.get_weight_log(user_id)
    goals = db.get_goals(user_id)
    favs = db.get_favourites(user_id)
    
    return render_template('admin_user_details.html', user=user, history=history, weight_log=weight_log, goals=goals, favs=favs)


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Delete a user permanently from the system."""
    db.delete_user(user_id)
    
    # Optional: Log them out if it happens to be the currently logged-in user
    if session.get('user_id') == user_id:
        session.clear()
        
    flash(f"User #{user_id} and all related logs were permanently deleted.", "success")
    return redirect(url_for('view_database'))


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
