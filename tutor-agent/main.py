from flask import Flask, request, jsonify
from flask_cors import CORS
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import bigquery

app = Flask(__name__)
CORS(app)

PROJECT_ID = "focus-mode-491514"
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.5-flash-lite")
bq_client = bigquery.Client(project=PROJECT_ID)

def log_to_bq(session_id, event_type, user_text, ai_text):
    if session_id == 'UNKNOWN_SESSION': return
    query = f"""
        INSERT INTO `{PROJECT_ID}.focus_db.session_logs` 
        (session_id, timestamp, event_type, user_text, ai_text)
        VALUES (@session, CURRENT_TIMESTAMP(), @event, @user, @ai)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("session", "STRING", session_id),
            bigquery.ScalarQueryParameter("event", "STRING", event_type),
            bigquery.ScalarQueryParameter("user", "STRING", user_text),
            bigquery.ScalarQueryParameter("ai", "STRING", ai_text)
        ]
    )
    bq_client.query(query, job_config=job_config).result()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        reason = data.get('reason', 'Unknown')
        session_id = data.get('session_id', 'UNKNOWN_SESSION')

        if user_message == "SYSTEM_TRIGGER_WARNING":
            warning_prompt = f"The student lost focus. Reason: '{reason}'. Write a single, polite, professional sentence telling them to get back to studying based on this specific action."
            response = model.generate_content(warning_prompt)
            ai_reply = "Warning: " + response.text
            log_to_bq(session_id, "WARNING", "System Warning Triggered", ai_reply)
            return jsonify({"reply": ai_reply})

        prompt = f"You are a professional AI Study Tutor. The user asks: '{user_message}'. Answer clearly and concisely."
        response = model.generate_content(prompt)
        ai_reply = response.text
        
        log_to_bq(session_id, "CHAT", user_message, ai_reply)
        return jsonify({"reply": ai_reply})
        
    except Exception as e:
        return jsonify({"reply": "System Error: " + str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        # Get a list of unique sessions and their start times
        query = f"SELECT session_id, MIN(timestamp) as start_time FROM `{PROJECT_ID}.focus_db.session_logs` GROUP BY session_id ORDER BY start_time DESC LIMIT 15"
        results = bq_client.query(query).result()
        sessions = [{"session_id": row.session_id, "start_time": row.start_time.strftime("%Y-%m-%d %H:%M:%S")} for row in results]
        return jsonify(sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    try:
        # Get all logs for a specific session
        query = f"SELECT timestamp, event_type, focus_score, distraction_reason, user_text, ai_text FROM `{PROJECT_ID}.focus_db.session_logs` WHERE session_id = @session_id ORDER BY timestamp ASC"
        job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("session_id", "STRING", session_id)])
        results = bq_client.query(query, job_config=job_config).result()
        
        logs = []
        for row in results:
            logs.append({
                "time": row.timestamp.strftime("%H:%M:%S"),
                "event": row.event_type,
                "score": row.focus_score,
                "reason": row.distraction_reason,
                "user": row.user_text,
                "ai": row.ai_text
            })
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)