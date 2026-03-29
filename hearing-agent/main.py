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

@app.route('/api/hearing', methods=['POST'])
def analyze_background_audio():
    try:
        data = request.json
        transcript = data.get('transcript', '')
        session_id = data.get('session_id', 'UNKNOWN_SESSION')

        # If the user was completely silent all session
        if not transcript.strip():
            return jsonify({"topics": "No audio recorded during this session."})

        # Tell Gemini to act as a summarizer
        prompt = f"""
        Analyze this background audio transcript from a student's study session:
        "{transcript}"
        
        What specific educational topics did the user learn or discuss? 
        Return a concise, comma-separated list of the main topics. If there is no educational content, reply with 'No clear educational topics detected'.
        """
        
        response = model.generate_content(prompt)
        topics = response.text.strip()

        # Log the learned topics into your unified BigQuery table
        if session_id != 'UNKNOWN_SESSION':
            query = f"""
                INSERT INTO `{PROJECT_ID}.focus_db.session_logs` 
                (session_id, timestamp, event_type, user_text, ai_text)
                VALUES (@session, CURRENT_TIMESTAMP(), 'HEARING_SUMMARY', 'Background Audio Transcript Processed', @topics)
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session", "STRING", session_id),
                    bigquery.ScalarQueryParameter("topics", "STRING", topics)
                ]
            )
            bq_client.query(query, job_config=job_config).result()
        
        return jsonify({"topics": topics})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)