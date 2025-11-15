import joblib
import pandas as pd
from flask import Flask, request, jsonify
from datetime import datetime
import numpy as np
import warnings
import os  # <-- Added
import re  # <-- Added
import requests  # <-- Added
from flask_cors import CORS  # <-- Added

# Suppress a specific UserWarning from sklearn about feature names
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.base")

# 1. Initialize the Flask app
app = Flask(__name__)
CORS(app)  # <-- Added: Enable CORS for all routes

# --- Load the "No-Show" Model Pipeline ---
try:
    # We use the pipeline file you created in the notebook
    MODEL_PATH = "models/xgb_show_no_show_pipeline.pkl"  # <-- Path updated as per your paste
    model_pipeline = joblib.load(MODEL_PATH)
    print(f"Model pipeline loaded successfully from {MODEL_PATH}")
except FileNotFoundError:
    print(f"Error: Model file not found at {MODEL_PATH}")
    model_pipeline = None
except Exception as e:
    print(f"Error loading model pipeline: {e}")
    model_pipeline = None

# --- Helper Functions for Symptom Guidance ---
# (Pasted from your second file)

def parse_guidance(text):
    """
    Parses the structured text response from the Cohere API.
    This is a direct Python port of your parseGuidance JavaScript function.
    """
    sections = {
        'assessment': '',
        'conditions': [],
        'recommendations': '',
        'urgency': '',
        'selfCare': '',
        'warnings': ''
    }
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    current_section = ''

    # Regex patterns for parsing conditions, matching the JS logic
    re_condition_1 = re.compile(r'^(\d+\.?\s*)?([^:]+):\s*(\d+%)', re.IGNORECASE)
    re_condition_2 = re.compile(r'^(\d+\.?\s*)?([^-]+)-\s*(\d+%)', re.IGNORECASE)
    re_bullet_or_number = re.compile(r'^[\d.\s•-]+')

    for line in lines:
        upper_line = line.upper()

        # Identify section headers
        if 'ASSESSMENT' in upper_line:
            current_section = 'assessment'
            colon_index = line.find(':')
            if colon_index != -1 and len(line) > colon_index + 1:
                sections['assessment'] += line[colon_index + 1:].strip() + ' '
            continue
        elif 'POSSIBLE CONDITIONS' in upper_line or 'CONDITIONS' in upper_line:
            current_section = 'conditions'
            continue
        elif 'RECOMMENDATIONS' in upper_line or 'IMMEDIATE RECOMMENDATIONS' in upper_line:
            current_section = 'recommendations'
            colon_index = line.find(':')
            if colon_index != -1 and len(line) > colon_index + 1:
                sections['recommendations'] += line[colon_index + 1:].strip() + ' '
            continue
        elif 'WHEN TO SEEK CARE' in upper_line or 'URGENCY' in upper_line:
            current_section = 'urgency'
            colon_index = line.find(':')
            if colon_index != -1 and len(line) > colon_index + 1:
                sections['urgency'] += line[colon_index + 1:].strip() + ' '
            continue
        elif 'SELF-CARE' in upper_line or 'SELF CARE' in upper_line:
            current_section = 'selfCare'
            colon_index = line.find(':')
            if colon_index != -1 and len(line) > colon_index + 1:
                sections['selfCare'] += line[colon_index + 1:].strip() + ' '
            continue
        elif 'WARNING SIGNS' in upper_line or 'RED FLAGS' in upper_line:
            current_section = 'warnings'
            colon_index = line.find(':')
            if colon_index != -1 and len(line) > colon_index + 1:
                sections['warnings'] += line[colon_index + 1:].strip() + ' '
            continue

        # Add content to the current section
        if current_section and line:
            if current_section == 'conditions':
                match_1 = re_condition_1.search(line)
                match_2 = re_condition_2.search(line)
                
                if match_1:
                    condition_name = match_1.group(2).strip()
                    percentage = match_1.group(3)
                    sections['conditions'].append(f"{condition_name}: {percentage}")
                elif match_2:
                    condition_name = match_2.group(2).strip()
                    percentage = match_2.group(3)
                    sections['conditions'].append(f"{condition_name}: {percentage}")
                elif '%' in line:
                    # Fallback for any line with a percentage
                    cleaned_line = re_bullet_or_number.sub('', line).strip()
                    sections['conditions'].append(cleaned_line)
                elif re_bullet_or_number.match(line):
                    # Fallback for numbered or bulleted items
                    cleaned_line = re_bullet_or_number.sub('', line).strip()
                    if cleaned_line:
                        sections['conditions'].append(cleaned_line)
            else:
                # Add content with a space, just like the JS version
                sections[current_section] += line + ' '

    # Clean up whitespace in string sections
    for key, value in sections.items():
        if isinstance(value, str):
            sections[key] = value.strip()

    return sections

def generate_fallback_conditions(symptoms):
    """
    Python port of your generateFallbackConditions function.
    """
    symptom_text = symptoms.lower()
    conditions = []
    
    if 'chest pain' in symptom_text or 'heart' in symptom_text:
        conditions.extend(['Angina: 45%', 'Myocardial Infarction: 25%', 'Costochondritis: 20%'])
    elif 'cough' in symptom_text and 'fever' in symptom_text:
        conditions.extend(['Pneumonia: 40%', 'Bronchitis: 35%', 'Upper Respiratory Infection: 25%'])
    elif 'headache' in symptom_text:
        if 'nausea' in symptom_text or 'vomit' in symptom_text:
            conditions.extend(['Migraine: 50%', 'Tension Headache: 30%', 'Sinusitis: 20%'])
        else:
            conditions.extend(['Tension Headache: 60%', 'Migraine: 25%', 'Dehydration: 15%'])
    elif 'fever' in symptom_text:
        conditions.extend(['Viral Infection: 60%', 'Bacterial Infection: 25%', 'Influenza: 15%'])
    elif 'abdominal' in symptom_text or 'stomach' in symptom_text:
        conditions.extend(['Gastroenteritis: 40%', 'Peptic Ulcer: 30%', 'IBS: 25%'])
    elif 'fatigue' in symptom_text or 'tired' in symptom_text:
        conditions.extend(['Viral Syndrome: 40%', 'Anemia: 30%', 'Thyroid Disorder: 25%'])
    elif 'rash' in symptom_text or 'skin' in symptom_text:
        conditions.extend(['Allergic Reaction: 45%', 'Dermatitis: 35%', 'Viral Exanthem: 20%'])
    elif 'joint' in symptom_text or 'arthritis' in symptom_text:
        conditions.extend(['Osteoarthritis: 50%', 'Rheumatoid Arthritis: 30%', 'Gout: 20%'])
    elif 'diarrhea' in symptom_text or 'bowel' in symptom_text:
        conditions.extend(['Gastroenteritis: 50%', 'IBS: 30%', 'Food Poisoning: 20%'])
    elif 'dizz' in symptom_text or 'vertigo' in symptom_text:
        conditions.extend(['Benign Vertigo: 45%', 'Hypotension: 30%', 'Inner Ear Infection: 25%'])
    else:
        conditions.extend(['Viral Infection: 40%', 'Common Cold: 35%', 'Stress-related Symptoms: 25%'])
    
    return conditions[:3]  # Limit to 3 conditions

def generate_fallback_recommendations(symptoms):
    """
    Python port of your generateFallbackRecommendations function.
    """
    symptom_text = symptoms.lower()
    
    if 'chest pain' in symptom_text:
        return 'Seek immediate medical attention. Avoid physical exertion. Take aspirin if not allergic (unless contraindicated).'
    elif 'fever' in symptom_text:
        return 'Rest and stay hydrated. Take acetaminophen or ibuprofen for fever reduction. Monitor temperature regularly.'
    elif 'headache' in symptom_text:
        return 'Rest in a dark, quiet room. Apply cold or warm compress. Stay hydrated. Consider over-the-counter pain relievers.'
    elif 'cough' in symptom_text:
        return 'Stay hydrated. Use honey or throat lozenges. Avoid irritants like smoke. Rest your voice.'
    else:
        return 'Rest and stay hydrated. Monitor symptoms closely. Take over-the-counter medications as needed for symptom relief.'

def generate_fallback_self_care(symptoms):
    """
    Python port of your generateFallbackSelfCare function.
    """
    symptom_text = symptoms.lower()
    tips = ['Stay well hydrated with water and clear fluids', 'Get adequate rest and sleep']
    
    if 'fever' in symptom_text:
        tips.extend(['Use cool compresses or lukewarm baths to reduce fever', 'Wear light, breathable clothing'])
    elif 'headache' in symptom_text:
        tips.extend(['Apply cold or warm compress to head or neck', 'Practice relaxation techniques'])
    elif 'cough' in symptom_text:
        tips.extend(['Use a humidifier or breathe steam from hot shower', 'Drink warm liquids like herbal tea with honey'])
    elif 'nausea' in symptom_text:
        tips.extend(['Eat bland foods like crackers or toast', 'Try ginger tea or peppermint'])
    else:
        tips.extend(['Maintain a healthy diet with fruits and vegetables', 'Avoid stress and practice gentle exercise if able'])
    
    return ' • '.join(tips)


# --- API Routes ---

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to confirm the server is running."""
    return {"status": "ok"}, 200

def preprocess_features(data):
    """
    Converts the raw JSON request data into the feature array 
    expected by the "No-Show" model pipeline.
    
    Based on your notebook, the features must be in this exact order: 
    ['Age', 'SMS_received', 'waiting_days', 'appointment_dow']
    """
    
    # 1. Age: Default to median (37) if missing or invalid
    try:
        # Use 37 as the default, which was the median in your notebook
        age = int(data.get('patient_age', 37))
        if age < 0:
            age = 37
    except (ValueError, TypeError):
        age = 37 

    # 2. SMS_received: Convert boolean (reminder_sent) to 0 or 1
    sms_received = 1 if data.get('reminder_sent', False) else 0

    # 3. waiting_days: Calculate from dates
    try:
        # Use pandas to_datetime for robust ISO string parsing
        scheduled_day = pd.to_datetime(data['booking_date'])
        appointment_day = pd.to_datetime(data['appointment_date'])
        
        # Calculate days as an integer
        waiting_days = (appointment_day - scheduled_day).days
        
        # Apply the same logic as your notebook: negative waits are set to 0
        if waiting_days < 0:
            waiting_days = 0
            
    except Exception as e:
        print(f"Date processing error: {e}. Defaulting waiting_days to 0.")
        waiting_days = 0 # Default on error

    # 4. appointment_dow: Get day of the week (Monday=0, Sunday=6)
    try:
        appointment_dow = appointment_day.dayofweek
    except Exception as e:
        print(f"Day of week processing error: {e}. Defaulting to 0 (Monday).")
        appointment_dow = 0 
        
    # Return as a 2D list for the pipeline's predict method
    feature_array = [age, sms_received, waiting_days, appointment_dow]
    return [feature_array]

@app.route("/predict", methods=["POST"])
def predict():
    """
    Receives appointment data, preprocesses it, and returns
    a "No-Show" prediction and confidence score.
    """
    if model_pipeline is None:
        return jsonify({"error": "No-Show Model is not loaded. Check server logs."}), 500

    try:
        data = request.json
        
        # 1. Pre-process the data into the correct feature format
        features = preprocess_features(data)
        
        # 2. Make the prediction
        prediction_raw = model_pipeline.predict(features)[0]
        
        # 3. Get the probability score
        probability = model_pipeline.predict_proba(features)[0][1]

        # 4. Convert to human-readable format
        prediction_label = "High Risk" if prediction_raw == 1 else "Low Risk"
            
        # 5. Send the JSON response
        return jsonify({
            "prediction": prediction_label,
            "confidence_score": float(probability) 
        }), 200

    except KeyError as e:
        print(f"Prediction failed due to missing key: {e}")
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except Exception as e:
        print(f"Prediction failed: {e}")
        return jsonify({"error": f"An error occurred during prediction: {str(e)}"}), 400

# --- NEW ROUTE for Symptom Guidance ---
@app.route('/generate_guidance', methods=['POST'])
def generate_guidance():
    """
    Main API endpoint to generate medical guidance using Cohere AI.
    """
    # 1. Get and validate input JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    symptoms = data.get('symptoms')
    gender = data.get('gender')
    age = data.get('age')

    if not all([symptoms, gender, age]):
        return jsonify({"error": "Missing required fields: symptoms, gender, age"}), 400

    # 2. Get API Key from environment
    api_key = os.environ.get('COHERE_API_KEY')
    if not api_key:
        print("Error: COHERE_API_KEY environment variable not set.")
        return jsonify({"error": "Server configuration error: API key not set"}), 500

    # 3. Construct the prompt for the API call
    api_prompt = f"""As a medical AI assistant, provide comprehensive medical guidance for a {age}-year-old {gender} experiencing the following symptoms: {symptoms}. Structure the response with clear headings: 'Assessment', 'Possible Conditions' (with likelihood percentages), 'Immediate Recommendations', 'When to Seek Care', 'Self-Care', and 'Red Flags'."""

    try:
        # 4. Make the API call to Cohere
        response = requests.post(
            "https://api.cohere.com/v2/chat",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "command-r", # Using a recommended model for this task
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": api_prompt
                    }
                ]
            },
            timeout=30 # Add a timeout for safety
        )
        
        # Raise an exception if the call was unsuccessful
        response.raise_for_status()
        
        api_response_data = response.json()
        
        # Extract the text content from the response
        generated_text = api_response_data.get('text', '')
        
        # 5. Parse the structured response
        guidance = parse_guidance(generated_text)

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        # --- Fallback Logic ---
        guidance = {
            'assessment': 'Could not connect to the AI medical assistant. The following is generalized guidance.',
            'conditions': generate_fallback_conditions(symptoms),
            'recommendations': generate_fallback_recommendations(symptoms),
            'urgency': 'If symptoms are severe or worsen, seek medical attention promptly.',
            'selfCare': generate_fallback_self_care(symptoms),
            'warnings': 'If you experience severe chest pain, difficulty breathing, or loss of consciousness, call emergency services immediately.'
        }
    
    # 6. Return the final parsed guidance
    return jsonify(guidance), 200


    # 4. Construct the request body for Cohere's Chat API
    cohere_data = {
        "model": "command-r", # Using a modern, recommended model
        "message": f"As a medical AI assistant, provide comprehensive medical guidance for a {age}-year-old {gender} experiencing the following symptoms: {symptoms}. Structure the response with clear headings like 'Assessment', 'Possible Conditions', 'Recommendations', 'Urgency', 'Self-Care', and 'Warning Signs'.",
        "stream": False
    }

    # 5. Make the request to Cohere API
    try:
        response = requests.post(
            "https://api.cohere.com/v1/chat", # Using the v1 chat endpoint
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=cohere_data
        )
        response.raise_for_status()  # This will raise an exception for HTTP errors (4xx or 5xx)
        
        api_response = response.json()
        
        # Extract the text from the response
        generated_text = api_response.get('text', '')

        if not generated_text:
            # Fallback if the 'text' key is missing or empty
            print("API response did not contain 'text'. Full response:", api_response)
            raise ValueError("Invalid response format from AI service")

    except requests.exceptions.RequestException as e:
        print(f"Error calling Cohere API: {e}")
        # Fallback logic if API fails
        fallback_conditions = generate_fallback_conditions(symptoms)
        fallback_recommendations = generate_fallback_recommendations(symptoms)
        fallback_self_care = generate_fallback_self_care(symptoms)
        
        return jsonify({
            "error": "Error communicating with the AI service. Using fallback guidance.",
            "guidance": {
                "assessment": "Could not generate a full AI assessment. The following is basic guidance.",
                "conditions": fallback_conditions,
                "recommendations": fallback_recommendations,
                "urgency": "If symptoms are severe or worsen, seek medical attention promptly.",
                "selfCare": fallback_self_care,
                "warnings": "Watch for signs of severe distress, such as difficulty breathing or chest pain, and seek immediate care if they occur."
            }
        }), 500
    
    # 6. Parse the response and return it
    parsed_guidance = parse_guidance(generated_text)
    
    return jsonify({"guidance": parsed_guidance}), 200

# --- Main entry point to run the app ---
if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible from the network.
    # The port 5001 is used to avoid conflicts with other services.
    # debug=True will auto-reload the server when you make changes.
    app.run(host='0.0.0.0', port=5001, debug=True)