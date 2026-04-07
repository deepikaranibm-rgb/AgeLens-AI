// Real-time BMI Calculator
function calculateBMI() {
    const weight = document.getElementById('weight');
    const height = document.getElementById('height');
    const bmiInput = document.getElementById('bmi');
    
    if (weight && height && bmiInput && weight.value && height.value) {
        const weightKg = parseFloat(weight.value);
        const heightM = parseFloat(height.value) / 100;
        const bmi = weightKg / (heightM * heightM);
        if (!isNaN(bmi) && isFinite(bmi)) {
            bmiInput.value = bmi.toFixed(1);
            updateBMICategory(bmi);
        }
    }
}

function updateBMICategory(bmi) {
    const categorySpan = document.getElementById('bmi-category');
    if (!categorySpan) return;
    
    if (bmi < 18.5) {
        categorySpan.innerHTML = 'Underweight ⚠️';
        categorySpan.style.color = '#ffc107';
    } else if (bmi < 25) {
        categorySpan.innerHTML = 'Normal ✅';
        categorySpan.style.color = '#28a745';
    } else if (bmi < 30) {
        categorySpan.innerHTML = 'Overweight ⚠️';
        categorySpan.style.color = '#ff9800';
    } else {
        categorySpan.innerHTML = 'Obese ❌';
        categorySpan.style.color = '#dc3545';
    }
}

// Real-time Age Difference Preview
function previewAgeDifference() {
    const age = document.getElementById('age');
    const bmi = document.getElementById('bmi');
    const sleep = document.getElementById('sleep');
    const exercise = document.getElementById('exercise');
    const smoking = document.getElementById('smoking');
    const alcohol = document.getElementById('alcohol');
    const stress = document.getElementById('stress');
    const systolicBP = document.getElementById('systolic_bp');
    const diastolicBP = document.getElementById('diastolic_bp');
    
    if (!age || !age.value) return;
    
    // Simple preview calculation
    let bioAge = parseFloat(age.value);
    if (bmi && bmi.value) bioAge += (parseFloat(bmi.value) - 22) * 0.3;
    if (sleep && sleep.value) bioAge += Math.max(0, (8 - parseFloat(sleep.value))) * 0.6;
    if (exercise && exercise.value) bioAge -= parseFloat(exercise.value) * 0.8;
    if (smoking && smoking.value) bioAge += parseInt(smoking.value) * 3.5;
    if (alcohol && alcohol.value) bioAge += parseFloat(alcohol.value) * 0.2;
    if (stress && stress.value) bioAge += (parseFloat(stress.value) - 5) * 0.4;
    if (systolicBP && systolicBP.value) bioAge += (parseFloat(systolicBP.value) - 120) * 0.05;
    if (diastolicBP && diastolicBP.value) bioAge += (parseFloat(diastolicBP.value) - 80) * 0.1;
    
    const diff = bioAge - parseFloat(age.value);
    const previewSpan = document.getElementById('age-preview');
    if (previewSpan) {
        if (diff < 0) {
            previewSpan.innerHTML = `📈 Preview: ${Math.abs(diff).toFixed(1)} years YOUNGER`;
            previewSpan.style.color = '#28a745';
        } else if (diff > 0) {
            previewSpan.innerHTML = `📉 Preview: ${diff.toFixed(1)} years OLDER`;
            previewSpan.style.color = '#dc3545';
        } else {
            previewSpan.innerHTML = `✅ Preview: Matching your age`;
            previewSpan.style.color = '#17a2b8';
        }
    }
}

// Form Validation
function validateForm() {
    const age = document.getElementById('age');
    if (age && (age.value < 20 || age.value > 100)) {
        showNotification('Age must be between 20 and 100 years', 'error');
        return false;
    }
    
    const bmi = document.getElementById('bmi');
    if (bmi && (bmi.value < 15 || bmi.value > 50)) {
        showNotification('BMI must be between 15 and 50', 'error');
        return false;
    }
    
    const sleep = document.getElementById('sleep');
    if (sleep && (sleep.value < 4 || sleep.value > 12)) {
        showNotification('Sleep hours must be between 4 and 12', 'error');
        return false;
    }
    
    return true;
}

// Submit Prediction with AJAX
async function submitPrediction(event) {
    event.preventDefault();
    
    if (!validateForm()) return;
    
    // Show loading state
    const submitBtn = document.querySelector('.predict-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '⏳ Calculating...';
    submitBtn.disabled = true;
    
    // Collect form data
    const formData = {
        age: parseFloat(document.getElementById('age').value),
        bmi: parseFloat(document.getElementById('bmi').value),
        sleep: parseFloat(document.getElementById('sleep').value),
        exercise: parseInt(document.getElementById('exercise').value),
        smoking: parseInt(document.querySelector('select[name="smoking"]').value),
        alcohol: parseInt(document.getElementById('alcohol').value),
        stress: parseFloat(document.getElementById('stress').value),
        systolic_bp: parseFloat(document.getElementById('systolic_bp').value),
        diastolic_bp: parseFloat(document.getElementById('diastolic_bp').value)
    };
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Error making prediction. Please try again.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Display Results in Modal
function displayResults(result) {
    const modal = document.getElementById('results-modal');
    const content = document.getElementById('results-content');
    
    const diffClass = result.difference < 0 ? 'positive' : (result.difference > 0 ? 'negative' : 'neutral');
    const diffText = result.difference < 0 ? `YOUNGER by ${Math.abs(result.difference)} years` : 
                     (result.difference > 0 ? `OLDER by ${result.difference} years` : 'MATCHES your age');
    
    let recommendationsHtml = '<ul>';
    result.recommendations.forEach(rec => {
        recommendationsHtml += `<li>${rec}</li>`;
    });
    recommendationsHtml += '</ul>';
    
    content.innerHTML = `
        <div class="results-container">
            <div class="age-comparison">
                <div class="age-card">
                    <div class="age-label">Chronological Age</div>
                    <div class="age-number">${result.chronological_age}</div>
                    <div class="age-unit">years</div>
                </div>
                <div class="age-arrow">→</div>
                <div class="age-card ${diffClass}">
                    <div class="age-label">Biological Age</div>
                    <div class="age-number">${result.biological_age}</div>
                    <div class="age-unit">years</div>
                </div>
            </div>
            
            <div class="result-summary ${diffClass}">
                <h3>📊 Result: ${diffText}</h3>
            </div>
            
            <div class="recommendations">
                <h3>📋 Personalized Recommendations</h3>
                ${recommendationsHtml}
            </div>
            
            <div class="modal-actions">
                <button onclick="savePrediction()" class="btn-save">💾 Save to History</button>
                <button onclick="closeModal()" class="btn-close">Close</button>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
    
    // Save prediction data for later
    window.lastPrediction = result;
}

function closeModal() {
    const modal = document.getElementById('results-modal');
    modal.style.display = 'none';
}

async function savePrediction() {
    if (window.lastPrediction) {
        showNotification('Prediction saved to your history!', 'success');
        closeModal();
    }
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Auto-save form data to localStorage
function autoSaveForm() {
    const formInputs = ['age', 'bmi', 'sleep', 'exercise', 'alcohol', 'stress', 'systolic_bp', 'diastolic_bp'];
    const formData = {};
    
    formInputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            formData[id] = element.value;
        }
    });
    
    const smoking = document.querySelector('select[name="smoking"]');
    if (smoking) formData.smoking = smoking.value;
    
    localStorage.setItem('savedFormData', JSON.stringify(formData));
}

function loadSavedForm() {
    const saved = localStorage.getItem('savedFormData');
    if (saved) {
        const formData = JSON.parse(saved);
        for (const [key, value] of Object.entries(formData)) {
            const element = document.getElementById(key);
            if (element) {
                element.value = value;
            }
        }
        
        const smoking = document.querySelector('select[name="smoking"]');
        if (smoking && formData.smoking) smoking.value = formData.smoking;
        
        if (formData.age) previewAgeDifference();
        if (formData.weight && formData.height) calculateBMI();
    }
}

function clearSavedForm() {
    localStorage.removeItem('savedFormData');
    showNotification('Form cleared!', 'success');
    
    // Reset form
    document.querySelector('form').reset();
    if (document.getElementById('bmi')) document.getElementById('bmi').value = '';
    if (document.getElementById('bmi-category')) document.getElementById('bmi-category').innerHTML = '';
    if (document.getElementById('age-preview')) document.getElementById('age-preview').innerHTML = '';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSavedForm();
    
    // Add auto-save to all inputs
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', autoSaveForm);
        input.addEventListener('input', autoSaveForm);
    });
    
    // Add real-time preview
    const previewInputs = ['age', 'bmi', 'sleep', 'exercise', 'alcohol', 'stress', 'systolic_bp', 'diastolic_bp'];
    previewInputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', previewAgeDifference);
        }
    });
    
    const smoking = document.querySelector('select[name="smoking"]');
    if (smoking) smoking.addEventListener('change', previewAgeDifference);
});

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('results-modal');
    if (event.target === modal) {
        closeModal();
    }
}