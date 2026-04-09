# 🚀 GCP AI Learning Portal

A full-stack, event-driven Learning Management System (LMS) powered by 4 independent AI microservices.

This platform uses Multimodal Vision telemetry, Background Audio processing, and Interactive Chat to monitor student focus, summarize learned topics, and generate custom pop-quizzes.

---

## 🏗️ Architecture

### 🌐 Frontend

* Vanilla HTML / CSS / JS
* Web Audio API
* WebRTC
* Light Theme UI

---

### ⚙️ Microservices (Python 3.13 / Flask)

* 👁️ **vision-agent**: Analyzes webcam frames for focus scoring
* 🤖 **tutor-agent**: Handles chatbot interactions, warnings, and analytics
* 👂 **hearing-agent**: Summarizes background audio into learning topics
* 📝 **quiz-agent**: Generates JSON-based quizzes

---

### ☁️ Cloud Infrastructure

* Google Cloud Run (Hosting)
* Vertex AI (Gemini 2.5 Flash)
* BigQuery (Database)

---

## 🛠️ Deployment Guide

### 🔐 Step 0: Open Google Cloud Console

1. Go to: https://console.cloud.google.com
2. Login using an account with **free trial credits**
3. Open **Cloud Shell** (top-right terminal icon)
4. Open **Cloud Shell Editor**
5. In editor:

   * Click **File (top-right)** → **Open Folder**
   * Open: `home/your_username`
6. Open terminal inside editor

---

### Step 1: Setup Cloud Shell

Run the following commands in terminal:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

---

### Step 2: Enable Required APIs

```bash
gcloud services enable run.googleapis.com aiplatform.googleapis.com bigquery.googleapis.com cloudbuild.googleapis.com
```

---

### Step 3: Clone Repository

```bash
git clone https://github.com/community-gdgvtu/GCP-AI-Learning-Portal.git
cd GCP-AI-Learning-Portal
```

---

### Step 4: Update Project ID

In all agent folders (`main.py`):

```python
PROJECT_ID = "your_project_id"
```

---

### Step 5: Setup BigQuery

1. Go to **Google Cloud Main Page**
2. Click **☰ Menu (top-left, three horizontal lines)**
3. Select **BigQuery**
4. Open a **New SQL Editor Tab**
5. Replace `YOUR_PROJECT_ID` with your actual project ID
6. Paste and run the following:

```sql
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
```

---

### Step 6: Deploy Microservices (IMPORTANT ORDER)

⚠️ Deploy services **sequentially in this exact order**

---

#### 📝 Quiz Agent

```bash
cd quiz-agent
gcloud run deploy quiz-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
```

👉 After deployment, copy the URL and update in **hearing-agent**:

```python
QUIZ_AGENT_URL = "https://your-quiz-api-url.com/api/quiz"
```

---

#### 🤖 Tutor Agent

```bash
cd ../tutor-agent
gcloud run deploy tutor-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
```

👉 After deployment, copy the URL and update in **vision-agent**:

```python
CHAT_AGENT_URL = "https://your-tutor-api-url.com/api/chat"
```

---

#### 👂 Hearing Agent

```bash
cd ../hearing-agent
gcloud run deploy hearing-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
```

---

#### 👁️ Vision Agent

```bash
cd ../vision-agent
gcloud run deploy vision-api --source . --region us-central1 --allow-unauthenticated --memory 2Gi --min-instances 1
```

---

### Step 7: Connect Frontend

Update `index.html`:

```javascript
const VISION_API_URL    = "https://vision-api-URL.run.app/api/vision";
const CHAT_API_URL      = "https://tutor-api-URL.run.app/api/chat";
const ANALYTICS_API_URL = "https://tutor-api-URL.run.app/api/sessions";
const HEARING_API_URL   = "https://hearing-api-URL.run.app/api/hearing";
const LOG_SCORE_URL     = "https://quiz-api-URL.run.app/api/log_score";
```

---

### Step 8: Create Dockerfile for Frontend

Create a new file named `Dockerfile` in your project directory and copy the following contents into it:

```dockerfile
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
```

---

### Step 9: Deploy Frontend

```bash
gcloud run deploy frontend-ui --source . --region us-central1 --allow-unauthenticated --port 80
```

👉 You will receive a **live HTTPS URL**

---

### Step 10: Run Platform

* Open frontend URL
* Allow camera & microphone
* Click **Start Session**

---

## 🎯 Features

* Real-time focus detection
* Audio-based learning insights
* AI-powered chatbot
* Automatic quiz generation
* Analytics using BigQuery

---

## 🧠 Tech Stack

* Frontend: HTML, CSS, JavaScript
* Backend: Python (Flask)
* AI: Vertex AI (Gemini)
* Cloud: Google Cloud Run
* Database: BigQuery
