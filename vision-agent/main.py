from flask import Flask, request, jsonify
from flask_cors import CORS
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import bigquery
import base64
import json
import datetime

app = Flask(__name__)
CORS(app)

PROJECT_ID = "focus-mode-491514"
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.5-flash-lite")
bq_client = bigquery.Client(project=PROJECT_ID)

@app.route('/api/vision', methods=['POST'])
def analyze_focus():
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        session_id = data.get('session_id', 'UNKNOWN_SESSION')
        
        image_part = Part.from_data(data=base64.b64decode(image_data), mime_type="image/jpeg")
        
        prompt = """
        Analyze this webcam frame of a student. Calculate a precise, granular 'focus_score' from 0 to 100 based on their eye gaze, posture, and presence of distractions.
        
        Provide a detailed 'reason' for this exact score. Be highly specific (e.g., "Looking directly at screen", "Looking slightly off-camera to the left", "Looking down at a mobile phone", "No one is in the frame", "Talking to someone off-screen", etc(other reasons depending on what he is actually doing)).
        
        If the score is strictly below 40, set the status to "Distracted". Otherwise, set it to "Focused".
        
        Respond ONLY with a valid JSON object. Format exactly like this:
        {"focus_score": 87, "status": "Focused", "reason": "Looking at screen but leaning back slightly"} 
        OR 
        {"focus_score": 15, "status": "Distracted", "reason": "Using a mobile phone below the desk"}
        """
        
        response = model.generate_content([image_part, prompt])
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(raw_text)

        # Log to BigQuery
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
                    bigquery.ScalarQueryParameter("reason", "STRING", result.get('reason', 'None'))
                ]
            )
            bq_client.query(query, job_config=job_config).result()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"focus_score": 0, "status": "Error", "reason": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)