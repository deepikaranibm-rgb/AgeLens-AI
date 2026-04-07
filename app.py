from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import bcrypt
import os
from bson import ObjectId
import json
from dotenv import load_dotenv
from flask import session

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# MongoDB Connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGODB_URI)
    db = client['biological_age_predictor']
    users_collection = db['users']
    predictions_collection = db['predictions']
    # Test connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB")
    mongo_connected = True
except Exception as e:
    print(f"❌ MongoDB error: {e}")
    users_collection = None
    predictions_collection = None
    mongo_connected = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']

@login_manager.user_loader
def load_user(user_id):
    if mongo_connected and users_collection is not None:
        try:
            user_data = users_collection.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except:
            pass
    return None

def calculate_biological_age(data):
    chron_age = float(data['chronological_age'])
    bmi = float(data['bmi'])
    sleep = float(data['sleep_hours'])
    exercise = int(data['exercise_frequency'])
    smoking = int(data['smoking'])
    alcohol = int(data['alcohol_consumption'])
    stress = float(data['stress_level'])
    systolic_bp = float(data['systolic_bp'])
    diastolic_bp = float(data['diastolic_bp'])
    
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

# ============= ROUTES =============

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if mongo_connected and users_collection is not None:
            user_data = users_collection.find_one({
                '$or': [{'username': username}, {'email': username}]
            })
            
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
                user = User(user_data)
                login_user(user)
                flash(f'Welcome {user.username}!', 'success')
                return redirect(url_for('dashboard'))
        
        flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))
        
        if mongo_connected and users_collection is not None:
            # Check if username exists
            if users_collection.find_one({'username': username}):
                flash('Username already taken!', 'error')
                return redirect(url_for('register'))
            
            # Check if email exists
            if users_collection.find_one({'email': email}):
                flash('Email already registered!', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users_collection.insert_one({
                'username': username,
                'email': email,
                'password': hashed,
                'created_at': datetime.now(),
                'predictions_count': 0
            })
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    predictions = []
    if mongo_connected and predictions_collection is not None:
        try:
            predictions = list(predictions_collection.find({'user_id': current_user.id}).sort('prediction_date', -1))
            for p in predictions:
                p['_id'] = str(p['_id'])
                if 'prediction_date' in p and hasattr(p['prediction_date'], 'isoformat'):
                    p['prediction_date'] = p['prediction_date'].isoformat()
        except Exception as e:
            print(f"Error: {e}")
    return render_template('dashboard.html', username=current_user.username, history=predictions)

@app.route('/predictor', methods=['GET', 'POST'])
@login_required
def predictor():
    if request.method == 'POST':
        try:
            # Get form data
            chron_age = float(request.form['age'])
            bmi = float(request.form['bmi'])
            sleep_hours = float(request.form['sleep'])
            exercise_frequency = int(request.form['exercise'])
            smoking = int(request.form['smoking'])
            alcohol_consumption = int(request.form['alcohol'])
            stress_level = float(request.form['stress'])
            systolic_bp = float(request.form['systolic_bp'])
            diastolic_bp = float(request.form['diastolic_bp'])
            
            # Calculate biological age
            bio_age = calculate_biological_age({
                'chronological_age': chron_age,
                'bmi': bmi,
                'sleep_hours': sleep_hours,
                'exercise_frequency': exercise_frequency,
                'smoking': smoking,
                'alcohol_consumption': alcohol_consumption,
                'stress_level': stress_level,
                'systolic_bp': systolic_bp,
                'diastolic_bp': diastolic_bp
            })
            
            # Save to database
            if mongo_connected and predictions_collection is not None:
                try:
                    predictions_collection.insert_one({
                        'user_id': current_user.id,
                        'chronological_age': chron_age,
                        'biological_age': bio_age,
                        'bmi': bmi,
                        'sleep_hours': sleep_hours,
                        'exercise_frequency': exercise_frequency,
                        'smoking': smoking,
                        'alcohol_consumption': alcohol_consumption,
                        'stress_level': stress_level,
                        'systolic_bp': systolic_bp,
                        'diastolic_bp': diastolic_bp,
                        'prediction_date': datetime.now()
                    })
                    
                    if users_collection is not None:
                        users_collection.update_one(
                            {'_id': ObjectId(current_user.id)},
                            {'$inc': {'predictions_count': 1}}
                        )
                except:
                    pass
            
            # Calculate difference
            age_diff = round(abs(bio_age - chron_age), 1)
            if bio_age < chron_age:
                status = "younger"
            elif bio_age > chron_age:
                status = "older"
            else:
                status = "same"
            
            # Generate recommendations
            recommendations = []
            if status == 'younger':
                recommendations.append("🎉 Excellent! Your biological age is younger than your chronological age!")
            elif status == 'older':
                recommendations.append("⚠️ Your biological age is higher. Consider lifestyle improvements.")
            else:
                recommendations.append("✅ Your biological age matches your chronological age!")
            
            if bmi > 25:
                recommendations.append("🏃 BMI is high. Consider regular exercise and balanced diet.")
            elif bmi < 18.5:
                recommendations.append("🍎 BMI is low. Focus on nutrient-rich foods.")
            
            if sleep_hours < 7:
                recommendations.append("😴 Sleep is below 7 hours. Aim for 7-9 hours.")
            
            if exercise_frequency < 3:
                recommendations.append("🏋️ Exercise frequency is low. Aim for 150 minutes weekly.")
            
            if smoking == 1:
                recommendations.append("🚭 Smoking increases biological age. Consider quitting.")
            
            if alcohol_consumption > 14:
                recommendations.append("🍷 High alcohol consumption. Limit to 1-2 drinks daily.")
            
            if stress_level > 7:
                recommendations.append("🧘 High stress levels. Try meditation or yoga.")
            
            if systolic_bp > 130 or diastolic_bp > 85:
                recommendations.append("❤️ Blood pressure is elevated. Reduce sodium intake.")
            
            # Get current date and time
            now = datetime.now()
            current_date = now.strftime('%B %d, %Y')
            current_time = now.strftime('%I:%M %p')
            current_year = now.year
            
            return render_template('result.html',
                                 chron_age=round(chron_age, 1),
                                 bio_age=round(bio_age, 1),
                                 age_diff=age_diff,
                                 status=status,
                                 recommendations=recommendations,
                                 username=current_user.username,
                                 bmi=bmi,
                                 sleep_hours=sleep_hours,
                                 exercise_frequency=exercise_frequency,
                                 systolic_bp=int(systolic_bp),
                                 diastolic_bp=int(diastolic_bp),
                                 current_date=current_date,
                                 current_time=current_time,
                                 current_year=current_year)
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('predictor'))
    
    return render_template('index.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
@app.route('/delete_history')
@login_required
def delete_history():
    if predictions_collection is not None:
        predictions_collection.delete_many({
            'user_id': current_user.id
        })
    flash('History deleted successfully!', 'success')
    return redirect(url_for('dashboard'))
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

def create_indexes():
    if mongo_connected:
        if users_collection is not None:
            try:
                users_collection.create_index([('username', 1)], unique=True)
                users_collection.create_index([('email', 1)], unique=True)
                print("✅ Indexes created for users collection")
            except Exception as e:
                print(f"⚠️ Error creating indexes: {e}")
        
        if predictions_collection is not None:
            try:
                predictions_collection.create_index([('user_id', 1), ('prediction_date', -1)])
                print("✅ Indexes created for predictions collection")
            except Exception as e:
                print(f"⚠️ Error creating indexes: {e}")
@app.route('/medical-report')
@login_required
def medical_report():
    # Get the most recent prediction for the current user
    if mongo_connected and predictions_collection is not None:
        try:
            latest_prediction = predictions_collection.find_one(
                {'user_id': current_user.id},
                sort=[('prediction_date', -1)]
            )
            
            if latest_prediction:
                chron_age = latest_prediction['chronological_age']
                bio_age = latest_prediction['biological_age']
                bmi = latest_prediction['bmi']
                sleep_hours = latest_prediction['sleep_hours']
                exercise_frequency = latest_prediction['exercise_frequency']
                smoking = latest_prediction['smoking']
                alcohol_consumption = latest_prediction['alcohol_consumption']
                stress_level = latest_prediction['stress_level']
                systolic_bp = latest_prediction['systolic_bp']
                diastolic_bp = latest_prediction['diastolic_bp']
                
                # Calculate difference and status
                age_diff = round(abs(bio_age - chron_age), 1)
                if bio_age < chron_age:
                    status = "younger"
                elif bio_age > chron_age:
                    status = "older"
                else:
                    status = "same"
                
                # Generate recommendations (same as in predictor)
                recommendations = []
                if status == 'younger':
                    recommendations.append("🎉 Excellent! Your biological age is younger than your chronological age!")
                elif status == 'older':
                    recommendations.append("⚠️ Your biological age is higher. Consider lifestyle improvements.")
                else:
                    recommendations.append("✅ Your biological age matches your chronological age!")
                
                if bmi > 25:
                    recommendations.append("🏃 BMI is high. Consider regular exercise and balanced diet.")
                elif bmi < 18.5:
                    recommendations.append("🍎 BMI is low. Focus on nutrient-rich foods.")
                
                if sleep_hours < 7:
                    recommendations.append("😴 Sleep is below 7 hours. Aim for 7-9 hours.")
                
                if exercise_frequency < 3:
                    recommendations.append("🏋️ Exercise frequency is low. Aim for 150 minutes weekly.")
                
                if smoking == 1:
                    recommendations.append("🚭 Smoking increases biological age. Consider quitting.")
                
                if alcohol_consumption > 14:
                    recommendations.append("🍷 High alcohol consumption. Limit to 1-2 drinks daily.")
                
                if stress_level > 7:
                    recommendations.append("🧘 High stress levels. Try meditation or yoga.")
                
                if systolic_bp > 130 or diastolic_bp > 85:
                    recommendations.append("❤️ Blood pressure is elevated. Reduce sodium intake.")
                
                # Get current date and time
                now = datetime.now()
                current_date = now.strftime('%B %d, %Y')
                current_time = now.strftime('%I:%M %p')
                
                # Generate unique report ID
                report_id = f"{current_user.id[:6]}{now.strftime('%Y%m%d%H%M%S')}"
                
                return render_template('medical_report.html',
                                     username=current_user.username,
                                     chron_age=round(chron_age, 1),
                                     bio_age=round(bio_age, 1),
                                     age_diff=age_diff,
                                     status=status,
                                     recommendations=recommendations,
                                     bmi=round(bmi, 1),
                                     sleep_hours=sleep_hours,
                                     exercise_frequency=exercise_frequency,
                                     smoking=smoking,
                                     alcohol_consumption=alcohol_consumption,
                                     stress_level=stress_level,
                                     systolic_bp=int(systolic_bp),
                                     diastolic_bp=int(diastolic_bp),
                                     current_date=current_date,
                                     current_time=current_time,
                                     report_id=report_id)
            else:
                flash('No predictions found. Please make a prediction first.', 'warning')
                return redirect(url_for('predictor'))
        except Exception as e:
            print(f"Error generating medical report: {e}")
            flash('Error generating report. Please try again.', 'error')
            return redirect(url_for('dashboard'))
    else:
        flash('Database connection error.', 'error')
        return redirect(url_for('predictor'))
@app.route('/delete-prediction/<prediction_id>', methods=['DELETE'])
@login_required
def delete_prediction(prediction_id):
    """Delete a single prediction by ID"""
    try:
        if mongo_connected and predictions_collection is not None:
            print(f"Deleting prediction with ID: {prediction_id}")  # Debug print
            
            # Convert string to ObjectId
            try:
                obj_id = ObjectId(prediction_id)
            except Exception as e:
                print(f"Invalid ObjectId: {prediction_id}, Error: {e}")
                return jsonify({'success': False, 'error': 'Invalid ID format'}), 400
            
            # Delete the prediction
            result = predictions_collection.delete_one({
                '_id': obj_id,
                'user_id': current_user.id
            })
            
            if result.deleted_count > 0:
                print(f"Successfully deleted prediction: {prediction_id}")
                return jsonify({'success': True, 'message': 'Prediction deleted successfully'})
            else:
                print(f"Prediction not found: {prediction_id}")
                return jsonify({'success': False, 'error': 'Prediction not found'}), 404
        else:
            return jsonify({'success': False, 'error': 'Database connection error'}), 500
    except Exception as e:
        print(f"Error in delete_prediction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
# Add language selection route
@app.route('/set-language/<lang>')
@login_required
def set_language(lang):
    if lang in ['en', 'kn', 'hi']:
        session['language'] = lang
    return redirect(request.referrer or url_for('dashboard'))

# Add a context processor to make language available in all templates
@app.context_processor
def inject_language():
    lang = session.get('language', 'en')
    return {'current_lang': lang}

if __name__ == '__main__':
    create_indexes()
    print("🚀 Starting Biological Age Predictor...")
    print("📍 Access at: http://localhost:8080")
    app.run(debug=True, host='127.0.0.1', port=8080)