# MindBloom - Mental Clarity & Growth Platform

MindBloom is a comprehensive mental health and productivity platform built with Django. It features a student portal for mood tracking and AI-guided growth, and a professional therapist portal for clinical management.

## 🚀 Features

- **Student Portal:** Mood tracking, AI journaling, task management, and mentor personas.
- **Therapist Portal:** Appointment scheduling, clinical notes, student wellness insights, and crisis management.
- **Admin Dashboard:** Real-time analytics, user management, and content CMS.
- **AI Integration:** Personalized reflections and pattern recognition powered by Google Gemini.

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.13+
- pip

### 2. Environment Setup
Clone the repository and create a virtual environment:
```bash
git clone <your-repo-url>
cd MindBloom
python -m venv venv
source venv/bin/scripts/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Note: Ensure you have a requirements.txt file. Create one with `pip freeze > requirements.txt` if needed.)*

### 4. Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_django_secret_key
DEBUG=True
GEMINI_API_KEY=your_google_gemini_api_key
```

### 5. Database Initialization
```bash
python manage.py migrate
python seed_resources.py  # If initial assets are needed
```

### 6. Run the Server
```bash
python manage.py runserver
```

## 🛡️ License
This project is for therapeutic and educational purposes only.
