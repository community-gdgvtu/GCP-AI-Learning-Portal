from flask import Flask, request, jsonify
from flask_cors import CORS
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import bigquery
import requests # NEW: Allows this server to talk to other servers!

app = Flask(__name__)
CORS(app)

PROJECT_ID = "focus-mode-491514"
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.5-flash-lite")
bq_client = bigquery.Client(project=PROJECT_ID)

# PASTE YOUR ACTUAL QUIZ API URL HERE
QUIZ_AGENT_URL = "https://your-quiz-api-url.com/api/quiz"

@app.route('/api/hearing', methods=['POST'])
def analyze_background_audio():
    try:
        data = request.json
        transcript = data.get('transcript', '')
        session_id = data.get('session_id', 'UNKNOWN_SESSION')
        num_questions = data.get('num_questions', 5) # Received from frontend

        if not transcript.strip():
            return jsonify({"topics": "No audio recorded.", "quiz_data": None})

        # 1. Generate Topics
        prompt = f"Analyze this background audio transcript: '{transcript}'. What specific educational topics did the user learn? Return a concise, comma-separated list."
        response = model.generate_content(prompt)
        topics = response.text.strip()

        # 2. Log Topics to BigQuery
        if session_id != 'UNKNOWN_SESSION':
            query = f"INSERT INTO `{PROJECT_ID}.focus_db.session_logs` (session_id, timestamp, event_type, user_text, ai_text) VALUES (@session, CURRENT_TIMESTAMP(), 'HEARING_SUMMARY', 'Background Audio Processed', @topics)"
            job_config = bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("session", "STRING", session_id),
                bigquery.ScalarQueryParameter("topics", "STRING", topics)
            ])
            bq_client.query(query, job_config=job_config).result()

        # 3. AGENT-TO-AGENT COMMUNICATION (A2A)
        # The Hearing Agent now securely calls the Quiz Agent behind the scenes!
        quiz_payload = {
            "topics": topics,
            "num_questions": int(num_questions),
            "session_id": session_id
        }
        
        quiz_response = requests.post(QUIZ_AGENT_URL, json=quiz_payload)
        quiz_data = quiz_response.json() if quiz_response.ok else {"status": "error", "message": "Quiz agent failed to respond."}

        # 4. Return everything back to the Frontend
        return jsonify({
            "topics": topics,
            "quiz_data": quiz_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)