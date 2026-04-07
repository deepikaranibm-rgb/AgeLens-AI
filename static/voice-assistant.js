// Voice Assistant for Biological Age Predictor
class VoiceAssistant {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.synth = window.speechSynthesis;
        this.currentUtterance = null;
        this.initSpeechRecognition();
    }

    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            this.recognition.maxAlternatives = 1;

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Heard:', transcript);
                this.processVoiceInput(transcript);
            };

            this.recognition.onerror = (event) => {
                console.error('Recognition error:', event.error);
                this.showNotification('🎤 Microphone error: ' + event.error, 'error');
                this.stopListening();
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.updateButtonUI();
            };
        } else {
            console.warn('Speech recognition not supported');
        }
    }

    startListening() {
        if (this.recognition && !this.isListening) {
            try {
                this.recognition.start();
                this.isListening = true;
                this.updateButtonUI();
                this.showNotification('🎤 Listening... Speak your health details', 'info');
                
                // Auto-stop after 8 seconds
                setTimeout(() => {
                    if (this.isListening) {
                        this.stopListening();
                    }
                }, 8000);
            } catch (e) {
                console.error('Error starting recognition:', e);
                this.showNotification('Please click the microphone button again', 'error');
            }
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            this.updateButtonUI();
        }
    }

    updateButtonUI() {
        const btn = document.getElementById('voiceAssistantBtn');
        const statusSpan = document.getElementById('voiceStatus');
        if (btn) {
            if (this.isListening) {
                btn.classList.add('listening');
                btn.innerHTML = '🎤 Listening... Stop';
                if (statusSpan) statusSpan.innerHTML = '🔴 Listening...';
            } else {
                btn.classList.remove('listening');
                btn.innerHTML = '🎤 Voice Assistant';
                if (statusSpan) statusSpan.innerHTML = '⚪ Click to speak';
            }
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('voiceNotification');
        if (notification) {
            notification.textContent = message;
            notification.className = `voice-notification ${type} show`;
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        } else {
            console.log(message);
        }
    }

    speak(text, onEnd = null) {
        if (this.synth) {
            // Cancel any ongoing speech
            if (this.currentUtterance) {
                this.synth.cancel();
            }
            
            this.currentUtterance = new SpeechSynthesisUtterance(text);
            this.currentUtterance.lang = 'en-US';
            this.currentUtterance.rate = 0.95;
            this.currentUtterance.pitch = 1.0;
            this.currentUtterance.volume = 1.0;
            
            // Select a natural voice if available
            let voices = this.synth.getVoices();
            const preferredVoice = voices.find(voice => voice.lang === 'en-US' && voice.name.includes('Google'));
            if (preferredVoice) {
                this.currentUtterance.voice = preferredVoice;
            }
            
            if (onEnd) {
                this.currentUtterance.onend = onEnd;
            }
            
            this.synth.speak(this.currentUtterance);
        }
    }

    processVoiceInput(transcript) {
        this.showNotification(`📝 You said: "${transcript}"`, 'info');
        this.parseHealthData(transcript);
    }

    parseHealthData(text) {
        const lowerText = text.toLowerCase();
        const extractedData = {};

        // Extract Age
        const ageMatch = text.match(/(\d+)\s*(?:years? old|yo|age)/i);
        if (ageMatch) {
            extractedData.age = parseInt(ageMatch[1]);
            this.fillField('age', extractedData.age);
        }

        // Extract BMI
        const bmiMatch = text.match(/bmi\s*(\d+\.?\d*)/i) || text.match(/body mass index\s*(\d+\.?\d*)/i);
        if (bmiMatch) {
            extractedData.bmi = parseFloat(bmiMatch[1]);
            this.fillField('bmi', extractedData.bmi);
        }

        // Extract Sleep Hours
        if (lowerText.includes('sleep') || lowerText.includes('sleeping')) {
            let sleepHours = null;
            const sleepMatch = text.match(/(\d+\.?\d*)\s*(?:hours?|hrs?)/i);
            if (sleepMatch) {
                sleepHours = parseFloat(sleepMatch[1]);
            } else if (lowerText.includes('less sleep') || lowerText.includes('sleep less')) {
                sleepHours = 5;
            } else if (lowerText.includes('good sleep') || lowerText.includes('enough sleep')) {
                sleepHours = 8;
            }
            if (sleepHours) {
                extractedData.sleep = sleepHours;
                this.fillField('sleep', sleepHours);
            }
        }

        // Extract Exercise
        if (lowerText.includes('exercise') || lowerText.includes('gym') || lowerText.includes('workout')) {
            let exerciseDays = null;
            const exerciseMatch = text.match(/(\d+)\s*(?:days?|times?)\s*(?:per|a)?\s*week/i);
            if (exerciseMatch) {
                exerciseDays = parseInt(exerciseMatch[1]);
            } else if (lowerText.includes('regularly') || lowerText.includes('daily')) {
                exerciseDays = 5;
            } else if (lowerText.includes('sometimes') || lowerText.includes('occasionally')) {
                exerciseDays = 2;
            } else if (lowerText.includes('never') || lowerText.includes('no exercise')) {
                exerciseDays = 0;
            }
            if (exerciseDays !== null) {
                extractedData.exercise = Math.min(7, Math.max(0, exerciseDays));
                this.fillField('exercise', extractedData.exercise);
            }
        }

        // Extract Smoking
        if (lowerText.includes('smoke')) {
            if (lowerText.includes('non') || lowerText.includes('never') || lowerText.includes('quit')) {
                extractedData.smoking = 0;
            } else {
                extractedData.smoking = 1;
            }
            this.fillField('smoking', extractedData.smoking);
        }

        // Extract Alcohol
        if (lowerText.includes('alcohol') || lowerText.includes('drink') || lowerText.includes('beer') || lowerText.includes('wine')) {
            let alcoholAmount = null;
            const alcoholMatch = text.match(/(\d+)\s*(?:drinks?|beers?|glasses?)/i);
            if (alcoholMatch) {
                alcoholAmount = parseInt(alcoholMatch[1]);
            } else if (lowerText.includes('moderate') || lowerText.includes('few drinks')) {
                alcoholAmount = 7;
            } else if (lowerText.includes('heavy') || lowerText.includes('many drinks')) {
                alcoholAmount = 20;
            } else if (lowerText.includes('no alcohol') || lowerText.includes('don\'t drink')) {
                alcoholAmount = 0;
            }
            if (alcoholAmount !== null) {
                extractedData.alcohol = Math.min(50, Math.max(0, alcoholAmount));
                this.fillField('alcohol', extractedData.alcohol);
            }
        }

        // Extract Stress
        if (lowerText.includes('stress')) {
            let stressLevel = null;
            const stressMatch = text.match(/stress\s*(\d+)/i);
            if (stressMatch) {
                stressLevel = parseInt(stressMatch[1]);
            } else if (lowerText.includes('very stressed') || lowerText.includes('high stress')) {
                stressLevel = 8;
            } else if (lowerText.includes('little stressed') || lowerText.includes('moderate stress')) {
                stressLevel = 5;
            } else if (lowerText.includes('no stress') || lowerText.includes('relaxed')) {
                stressLevel = 2;
            }
            if (stressLevel !== null) {
                extractedData.stress = Math.min(10, Math.max(1, stressLevel));
                this.fillField('stress', extractedData.stress);
            }
        }

        // Extract Blood Pressure
        const bpMatch = text.match(/(\d+)\s*(?:over|by|\/)\s*(\d+)/i);
        if (bpMatch) {
            extractedData.systolic_bp = parseInt(bpMatch[1]);
            extractedData.diastolic_bp = parseInt(bpMatch[2]);
            this.fillField('systolic_bp', extractedData.systolic_bp);
            this.fillField('diastolic_bp', extractedData.diastolic_bp);
        }

        // Provide feedback on what was filled
        const filledCount = Object.keys(extractedData).length;
        if (filledCount > 0) {
            this.speak(`I've filled ${filledCount} fields based on what you said. You can review and adjust them before predicting.`);
        } else {
            this.speak("I didn't catch specific numbers. Please try saying something like 'I am 30 years old, BMI 24, sleep 7 hours, exercise 3 days a week'.");
        }

        // Auto-calculate BMI if weight and height are available
        this.autoCalculateBMI();

        return extractedData;
    }

    fillField(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
            field.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Add visual feedback
            field.classList.add('voice-filled');
            setTimeout(() => {
                field.classList.remove('voice-filled');
            }, 1000);
        }
    }

    autoCalculateBMI() {
        const weight = document.getElementById('weight');
        const height = document.getElementById('height');
        const bmiField = document.getElementById('bmi');
        
        if (weight && height && bmiField && weight.value && height.value) {
            const weightKg = parseFloat(weight.value);
            const heightM = parseFloat(height.value) / 100;
            if (weightKg > 0 && heightM > 0) {
                const bmi = weightKg / (heightM * heightM);
                bmiField.value = bmi.toFixed(1);
                bmiField.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    }

    // Speak the prediction results
    speakPredictionResults(data) {
        const { bio_age, chron_age, status, age_diff, recommendations } = data;
        
        let message = `Your biological age is ${bio_age} years. `;
        message += `Your chronological age is ${chron_age} years. `;
        
        if (status === 'younger') {
            message += `Congratulations! You are ${age_diff} years younger biologically. `;
            message += `Your healthy lifestyle is paying off. Keep up the great work! `;
        } else if (status === 'older') {
            message += `Your biological age is ${age_diff} years older than your chronological age. `;
            message += `Don't worry! Small lifestyle changes can make a big difference. `;
        } else {
            message += `Your biological age matches your chronological age perfectly! `;
            message += `You're on the right track for healthy aging. `;
        }
        
        // Add top 2 recommendations
        if (recommendations && recommendations.length > 0) {
            message += `Here are my recommendations for you. `;
            const topRecs = recommendations.slice(0, 2);
            topRecs.forEach(rec => {
                message += rec.replace(/[^a-zA-Z0-9\s]/g, '') + '. ';
            });
        }
        
        this.speak(message);
    }

    // Welcome message for result page
    welcomeToResults() {
        this.speak("Here are your biological age prediction results. I'll read them out for you.");
    }
}

// Initialize voice assistant when page loads
let voiceAssistant = null;

document.addEventListener('DOMContentLoaded', () => {
    voiceAssistant = new VoiceAssistant();
    
    // Add voice button to the page if it doesn't exist
    addVoiceButton();
});

function addVoiceButton() {
    // Voice button disabled - remove this function or leave empty
    return;
}

function toggleVoiceAssistant() {
    if (voiceAssistant) {
        if (voiceAssistant.isListening) {
            voiceAssistant.stopListening();
        } else {
            voiceAssistant.startListening();
        }
    }
}

function addVoiceStyles() {
    if (!document.getElementById('voiceStyles')) {
        const style = document.createElement('style');
        style.id = 'voiceStyles';
        style.textContent = `
            .voice-assistant-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 50px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .voice-assistant-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            
            .voice-assistant-btn.listening {
                background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                animation: pulse 1.5s infinite;
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
                100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
            }
            
            .voice-status {
                font-size: 11px;
                text-align: center;
                margin-top: 5px;
                color: #666;
                background: white;
                padding: 2px 8px;
                border-radius: 20px;
            }
            
            .voice-notification {
                position: fixed;
                bottom: 100px;
                right: 20px;
                background: #333;
                color: white;
                padding: 10px 15px;
                border-radius: 10px;
                font-size: 14px;
                max-width: 300px;
                z-index: 999;
                opacity: 0;
                transition: opacity 0.3s;
                pointer-events: none;
            }
            
            .voice-notification.show {
                opacity: 1;
            }
            
            .voice-notification.info {
                background: #667eea;
            }
            
            .voice-notification.error {
                background: #dc3545;
            }
            
            .voice-notification.success {
                background: #28a745;
            }
            
            .voice-filled {
                animation: voiceFillFlash 0.5s ease;
                border-color: #28a745 !important;
                background-color: rgba(40, 167, 69, 0.1) !important;
            }
            
            @keyframes voiceFillFlash {
                0% { transform: scale(1); }
                50% { transform: scale(1.02); }
                100% { transform: scale(1); }
            }
            
            /* Microphone button on forms */
            .voice-input-group {
                position: relative;
            }
            
            .mic-btn {
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                padding: 5px;
                border-radius: 50%;
                transition: all 0.3s;
            }
            
            .mic-btn:hover {
                background: #f0f0f0;
                transform: translateY(-50%) scale(1.1);
            }
        `;
        document.head.appendChild(style);
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceAssistant;
}