GCP AI Learning Portal
A full-stack, event-driven Learning Management System (LMS) powered by 4 independent AI microservices. This platform uses Multimodal Vision telemetry, Background Audio processing, and Interactive Chat to monitor student focus, summarize learned topics, and generate custom pop-quizzes.

🏗️ Architecture
Frontend: Vanilla HTML/CSS/JS (Light Theme, Web Audio API, WebRTC)

Microservices (Python 3.13 / Flask):

👁️ vision-agent: Analyzes webcam frames for focus scoring.

🤖 tutor-agent: Handles chatbot interactions, warnings, and BigQuery analytics.

👂 hearing-agent: Summarizes background audio into learned topics.

📝 quiz-agent: Generates JSON-based exams based on hearing topics.

Cloud Infrastructure: Google Cloud Run (Hosting), Vertex AI (Gemini 2.5 Flash), BigQuery (Database).

🛠️ Step-by-Step Deployment Guide
Step 1: Prepare Google Cloud Shell
Log into your Google Cloud Console.

Open Cloud Shell (the >_ terminal icon in the top right).

Authenticate your account:

Bash
gcloud auth login
Set your active Project ID (Replace YOUR_PROJECT_ID with your actual GCP Project ID):

Bash
gcloud config set project YOUR_PROJECT_ID
Step 2: Enable Required GCP APIs
Your Google Cloud project needs permission to use Cloud Run, Vertex AI, BigQuery, and Cloud Build. Run this command to enable them all instantly:

Bash
gcloud services enable run.googleapis.com aiplatform.googleapis.com bigquery.googleapis.com cloudbuild.googleapis.com
Step 3: Clone the Repository
Pull the code into your Cloud Shell environment:

Bash
git clone https://github.com/YOUR_USERNAME/GCP-AI-Learning-Portal.git
cd GCP-AI-Learning-Portal
Step 4: Update the Code with YOUR Project ID
The Python code needs to know your specific Project ID to access Vertex AI and BigQuery.

Open the Cloud Shell Editor.

In all four agent folders (vision-agent, tutor-agent, hearing-agent, quiz-agent), open the main.py file.

Change this line in every file to match your project:

Python
PROJECT_ID = "YOUR_PROJECT_ID" 
Step 5: Setup the BigQuery Database
We need to create the focus_db dataset and the session_logs master table.

Go to the BigQuery page in the Google Cloud Console.

Click SQL Workspace and paste/run this exact query (Replace YOUR_PROJECT_ID):

SQL
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.focus_db`;

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.focus_db.session_logs` (
  session_id STRING,
  timestamp TIMESTAMP,
  event_type STRING,
  focus_score INT64,
  distraction_reason STRING,
  user_text STRING,
  ai_text STRING
);
Step 6: Deploy the 4 Microservices to Cloud Run
Deploy each agent to the cloud. We use --min-instances 1 to prevent "Cold Starts," ensuring the AI responds with zero latency.

Deploy Vision Agent:

Bash
cd ~/GCP-AI-Learning-Portal/vision-agent
gcloud run deploy vision-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
Deploy Tutor Agent:

Bash
cd ../tutor-agent
gcloud run deploy tutor-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
Deploy Hearing Agent:

Bash
cd ../hearing-agent
gcloud run deploy hearing-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
Deploy Quiz Agent:

Bash
cd ../quiz-agent
gcloud run deploy quiz-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
(⚠️ Make sure to copy the 4 green URLs that Cloud Run generates after each successful deployment!)

Step 7: Connect the Frontend
Open index.html in your editor.

Scroll down to the <script> section (around line 170).

Paste your 4 new Cloud Run URLs into the constant variables:

JavaScript
const VISION_API_URL    = "https://vision-api-YOUR-LINK.run.app/api/vision";
const CHAT_API_URL      = "https://tutor-api-YOUR-LINK.run.app/api/chat";
const ANALYTICS_API_URL = "https://tutor-api-YOUR-LINK.run.app/api/sessions"; 
const HEARING_API_URL   = "https://hearing-api-YOUR-LINK.run.app/api/hearing"; 
const QUIZ_API_URL      = "https://quiz-api-YOUR-LINK.run.app/api/quiz"; 
const LOG_SCORE_URL     = "https://quiz-api-YOUR-LINK.run.app/api/log_score"; 
(Note: Analytics uses the Tutor API URL, and Log Score uses the Quiz API URL).

Step 8: Run the Platform!
Because modern web browsers block webcams and microphones on unverified cloud instances, you must run the frontend locally:

Download the updated index.html file to your personal computer.

Double-click it to open it in Google Chrome or Microsoft Edge.

Click Start Session, grant camera/microphone permissions, and start learning!
