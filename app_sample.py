from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chronological_age REAL,
            biological_age REAL,
            bmi REAL,
            sleep_hours REAL,
            exercise_frequency INTEGER,
            smoking INTEGER,
            alcohol_consumption INTEGER,
            stress_level REAL,
            systolic_bp REAL,
            diastolic_bp REAL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def calculate_biological_age(data):
    chron_age = data['chronological_age']
    bmi = data['bmi']
    sleep = data['sleep_hours']
    exercise = data['exercise_frequency']
    smoking = data['smoking']
    alcohol = data['alcohol_consumption']
    stress = data['stress_level']
    systolic_bp = data['systolic_bp']
    diastolic_bp = data['diastolic_bp']
    
    bio_age = chron_age
    bio_age += (bmi - 22) * 0.3
    bio_age += max(0, (8 - sleep)) * 0.6
    bio_age -= exercise * 0.8
    bio_age += smoking * 3.5
    bio_age += alcohol * 0.2
    bio_age += (stress - 5) * 0.4
    bio_age += (systolic_bp - 120) * 0.05
    bio_age += (diastolic_bp - 80) * 0.1
    
    return max(chron_age - 15, min(bio_age, chron_age + 20))

def add_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute(
        'SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?',
        (username, username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))
        
        user_id = add_user(username, email, password)
        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists!', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/predictor', methods=['GET', 'POST'])
def predictor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            data = {
                'chronological_age': float(request.form['age']),
                'bmi': float(request.form['bmi']),
                'sleep_hours': float(request.form['sleep']),
                'exercise_frequency': int(request.form['exercise']),
                'smoking': int(request.form['smoking']),
                'alcohol_consumption': int(request.form['alcohol']),
                'stress_level': float(request.form['stress']),
                'systolic_bp': float(request.form['systolic_bp']),
                'diastolic_bp': float(request.form['diastolic_bp'])
            }
            
            bio_age = calculate_biological_age(data)
            age_diff = bio_age - data['chronological_age']
            status = "younger" if age_diff < 0 else "older" if age_diff > 0 else "same"
            
            return render_template('result.html',
                                 chron_age=round(data['chronological_age'], 1),
                                 bio_age=round(bio_age, 1),
                                 age_diff=abs(round(age_diff, 1)),
                                 status=status)
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('predictor'))
    
    return render_template('predictor.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5500)