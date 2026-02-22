---
title: MindBloom
emoji: 💎
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: true
---

# MindBloom: AI-Powered Mental Health Platform 💎🛡️🏛️

**MindBloom** is a next-generation mental wellness and clinical management system. It bridges the gap between AI-driven self-reflection and professional therapeutic care, providing a secure, data-driven ecosystem for both students and healthcare providers.

## 🌟 The Portals

### 🎓 Student Sanctuary
A premium, glassmorphism-inspired space for personal growth.
- **AI Mentorship:** Personalized reflections powered by Google Gemini (Zen, Strategist, Catalyst, and Listener personas).
- **Daily Mood Alchemy:** Beautifully designed mood and energy tracking with trend analysis.
- **Focus Timer:** Built-in productivity tools for mindful studying.

### 👩‍⚕️ Professional Therapist Portal (Vetted & SECURE)
A secure clinical environment for approved healthcare providers.
- **Database Accurate Insights:** Real-time engagement, retention, and crisis frequency analytics.
- **Clinical Records:** Secure student connection management with encrypted session notes.
- **Crisis Monitoring:** Automated alert system for proactive intervention.
- **Approval Workflow:** Locked professional access requiring manual administrative vetting.

### 🏛️ Admin Command Center
A high-level dashboard for platform governance.
- **User Management:** Full control over role promotions and professional approvals.
- **Global Analytics:** Data-driven metrics on community wellness and system growth.
- **Security Hub:** Hard-locked professional registration to prevent unauthorized access.

## 🛠️ Infrastructure & Security

- **Persistent Storage:** Configured for Hugging Face official `/data` volumes, ensuring no data loss during re-deployments. 💾
- **Invite-Only Professional Network:** All therapists must be manually promoted and approved by the site owner. 🔓
- **Dockerized Stability:** High-availability environment optimized for Hugging Face Spaces.
- **Security Hardening:** CSRF protection, secure cookie handling, and role-based access control (RBAC).

## 🚀 Deployment (Hugging Face Spaces)

1. **Enable Persistent Storage:** Go to *Settings > Persistent Storage* and select a tier (Small is recommended).
2. **Environment Variables:**
   - `ADMIN_USERNAME`: Your master admin user.
   - `ADMIN_PASSWORD`: Your secure admin password.
   - `GEMINI_API_KEY`: Your Google AI API key.
3. **Push to HF:**
   ```powershell
   git push hf main
   ```

## 🛠️ Local Development

```bash
# Clone & Setup
git clone <repo-url>
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows

# Install & Migrate
pip install -r requirements.txt
python manage.py migrate

# Start Engine
python manage.py runserver
```

## 🛡️ Ethics & Safety
MindBloom is designed for wellness and clinical augmentation. It features automated **Crisis Detection** to flag high-risk journal entries directly to connected therapists.

---
*Developed with a focus on Privacy, Empathy, and Clinical Precision.* 💎🚀🎯
