from flask import Flask, request, jsonify
from flask_cors import CORS
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import bigquery
import base64
import json
import requests # NEW: Allows Server-to-Server communication

app = Flask(__name__)
CORS(app)

PROJECT_ID = "your_project_id"
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.5-flash-lite")
bq_client = bigquery.Client(project=PROJECT_ID)

# PASTE YOUR ACTUAL TUTOR/CHAT API URL HERE
CHAT_AGENT_URL = "https://your-tutor-api-url.com/api/chat"

@app.route('/api/vision', methods=['POST'])
def analyze_focus():
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        session_id = data.get('session_id', 'UNKNOWN_SESSION')
        previous_status = data.get('previous_status', 'Focused') # The frontend tells us how the user was doing 6 seconds ago
        
        image_part = Part.from_data(data=base64.b64decode(image_data), mime_type="image/jpeg")
        
        prompt = """
        Analyze this webcam frame of a student. Calculate a precise, granular 'focus_score' from 0 to 100 based on their eye gaze, posture, and presence of distractions.
        Provide a detailed 'reason' for this exact score. Be highly specific.
        If the score is strictly below 40, set the status to "Distracted". Otherwise, set it to "Focused".
        Respond ONLY with a valid JSON object. Format exactly like this:
        {"focus_score": 87, "status": "Focused", "reason": "Looking at screen but leaning back slightly"} 
        """
        
        response = model.generate_content([image_part, prompt])
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(raw_text)

        new_status = result.get('status', 'Unknown')
        reason = result.get('reason', 'None')
        warning_message = None # Defaults to none

        # 1. Log Vision Check to BigQuery
        if session_id != 'UNKNOWN_SESSION':
            query = f"""
                INSERT INTO `{PROJECT_ID}.focus_db.session_logs` 
                (session_id, timestamp, event_type, focus_score, distraction_reason)
                VALUES (@session, CURRENT_TIMESTAMP(), 'FOCUS_CHECK', @score, @reason)
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session", "STRING", session_id),
                    bigquery.ScalarQueryParameter("score", "INTEGER", result.get('focus_score', 0)),
                    bigquery.ScalarQueryParameter("reason", "STRING", reason)
                ]
            )
            bq_client.query(query, job_config=job_config).result()

        # 2. AGENT-TO-AGENT COMMUNICATION (A2A)
        # If the user JUST got distracted, the Vision Agent securely calls the Chatbot Agent directly!
        if new_status == "Distracted" and previous_status == "Focused":
            chat_payload = {
                "message": "SYSTEM_TRIGGER_WARNING",
                "reason": reason,
                "session_id": session_id
            }
            try:
                chat_response = requests.post(CHAT_AGENT_URL, json=chat_payload)
                if chat_response.ok:
                    warning_message = chat_response.json().get('reply')
            except Exception as e:
                print("A2A connection failed:", e)

        # 3. Send the vision stats AND the AI generated warning back to the browser
        result['warning_message'] = warning_message
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"focus_score": 0, "status": "Error", "reason": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
