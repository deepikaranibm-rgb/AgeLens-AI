import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

def generate_synthetic_data(n_samples=5000):
    """
    Generate synthetic health data based on biological age formula
    Biological age = Chronological age + lifestyle adjustments
    """
    np.random.seed(42)
    
    # Chronological age (20-80 years)
    chron_age = np.random.uniform(20, 80, n_samples)
    
    # Lifestyle factors
    bmi = np.random.normal(25, 5, n_samples)  # BMI around 25
    bmi = np.clip(bmi, 15, 45)  # Clip extreme values
    
    sleep_hours = np.random.normal(7, 1.5, n_samples)
    sleep_hours = np.clip(sleep_hours, 4, 12)
    
    exercise_freq = np.random.poisson(3, n_samples)  # 0-7 days/week
    exercise_freq = np.clip(exercise_freq, 0, 7)
    
    smoking = np.random.choice([0, 1], n_samples, p=[0.8, 0.2])  # 20% smokers
    
    alcohol_consumption = np.random.poisson(4, n_samples)  # drinks/week
    alcohol_consumption = np.clip(alcohol_consumption, 0, 30)
    
    stress_level = np.random.uniform(1, 10, n_samples)  # 1-10 scale
    
    # Health markers
    systolic_bp = np.random.normal(120, 15, n_samples)
    systolic_bp = np.clip(systolic_bp, 90, 200)
    
    diastolic_bp = np.random.normal(80, 10, n_samples)
    diastolic_bp = np.clip(diastolic_bp, 60, 120)
    
    # Calculate Biological Age
    # Positive factors increase biological age, negative factors decrease it
    bio_age = chron_age.copy()
    
    # BMI effect (optimal 22)
    bio_age += (bmi - 22) * 0.3
    
    # Sleep effect (optimal 7-8 hours)
    sleep_deviation = np.abs(sleep_hours - 7.5)
    bio_age += sleep_deviation * 0.8
    
    # Exercise effect (more is better)
    bio_age -= exercise_freq * 0.7
    
    # Smoking effect
    bio_age += smoking * 3.5
    
    # Alcohol effect
    bio_age += alcohol_consumption * 0.2
    
    # Stress effect
    bio_age += (stress_level - 5) * 0.4
    
    # Blood pressure effect
    bp_effect = (systolic_bp - 120) * 0.05 + (diastolic_bp - 80) * 0.1
    bio_age += np.clip(bp_effect, -5, 10)
    
    # Add some noise
    bio_age += np.random.normal(0, 1.5, n_samples)
    
    # Create DataFrame
    df = pd.DataFrame({
        'chronological_age': chron_age,
        'bmi': bmi,
        'sleep_hours': sleep_hours,
        'exercise_frequency': exercise_freq,
        'smoking': smoking,
        'alcohol_consumption': alcohol_consumption,
        'stress_level': stress_level,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'biological_age': bio_age
    })
    
    return df

def train_model():
    """Train the biological age prediction model"""
    print("📊 Generating synthetic health data...")
    df = generate_synthetic_data(10000)
    
    print(f"✅ Generated {len(df)} samples")
    print(df.head())
    
    # Features for prediction
    features = [
        'chronological_age', 'bmi', 'sleep_hours', 
        'exercise_frequency', 'smoking', 'alcohol_consumption',
        'stress_level', 'systolic_bp', 'diastolic_bp'
    ]
    
    X = df[features]
    y = df['biological_age']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    print("🤖 Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n📈 Model Performance:")
    print(f"   Mean Absolute Error: {mae:.2f} years")
    print(f"   R² Score: {r2:.3f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔑 Top 5 Important Features:")
    print(feature_importance.head())
    
    # Save model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/biological_age_model.pkl')
    print("\n💾 Model saved to 'models/biological_age_model.pkl'")
    
    return model

if __name__ == '__main__':
    train_model()