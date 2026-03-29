from flask import Flask, request, jsonify
from flask_cors import CORS
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import bigquery
import json

app = Flask(__name__)
CORS(app)

PROJECT_ID = "focus-mode-491514"
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.5-flash-lite")
bq_client = bigquery.Client(project=PROJECT_ID)

@app.route('/api/quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.json
        topics = data.get('topics', '')
        num_questions = int(data.get('num_questions', 5))

        if not topics or "No clear educational topics" in topics:
            return jsonify({"status": "skipped", "message": "No topics detected to test."})

        prompt = f"""
        The student just finished studying these topics: "{topics}".
        Generate exactly {num_questions} multiple-choice questions to test their knowledge.
        
        Respond ONLY with a valid JSON array of objects. Do not include formatting like ```json.
        Format EXACTLY like this:
        [
          {{"question": "...", "options": ["A", "B", "C", "D"], "answer": "Exact text of the correct option", "explanation": "..."}}
        ]
        """
        
        response = model.generate_content(prompt)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        questions = json.loads(raw_text)
        
        return jsonify({"status": "success", "questions": questions})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/log_score', methods=['POST'])
def log_score():
    try:
        data = request.json
        session_id = data.get('session_id', 'UNKNOWN_SESSION')
        score_summary = data.get('score_summary', '0/0')
        
        if session_id != 'UNKNOWN_SESSION':
            query = f"""
                INSERT INTO `{PROJECT_ID}.focus_db.session_logs` 
                (session_id, timestamp, event_type, user_text, ai_text)
                VALUES (@session, CURRENT_TIMESTAMP(), 'EXAM_RESULT', 'Post-Session Exam Completed', @score)
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session", "STRING", session_id),
                    bigquery.ScalarQueryParameter("score", "STRING", score_summary)
                ]
            )
            bq_client.query(query, job_config=job_config).result()
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)