# Securing Systems with Explainable AI-Enabled Zero Trust Security and Post-Incident Digital Forensics Investigation

## Step 1 status: Project skeleton + MySQL schema + Auth + real-time login logging

### Setup

1. **Create a virtual environment**
   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/Mac
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Create the MySQL database** (in MySQL Workbench or CLI)
   ```sql
   CREATE DATABASE ztxai_db;
   ```

4. **Configure environment variables**
   Copy `.env.example` to `.env` and fill in your real MySQL password:
   ```
   cp .env.example .env
   ```

5. **Run the app**
   ```
   python run.py
   ```
   This auto-creates all tables (users, login_events, evidence_logs) on
   first run. Visit http://127.0.0.1:5000/register to create an account,
   then log in.

### What's implemented so far
- User registration (hashed passwords, never stored in plaintext)
- Login / logout via Flask-Login (session cookie based)
- **Every login attempt** (success or fail) is written to `login_events`
  with IP address, device/user-agent, and timestamp — this table is the
  data source for every ML step that follows.
- Placeholder dashboard confirming the session works end-to-end.

### What's NOT implemented yet (coming in later steps)
- Synthetic log generator (Step 3)
- Feature extraction (Step 4)
- Isolation Forest / Random Forest / K-Means (Steps 5–7)
- SHAP explainability (Step 9)
- Adaptive access control — OTP/Block (Step 10)
- Forensic evidence hashing, timeline, PDF reports (Step 11)
- Full Chart.js dashboard (Step 12)

### Folder structure
```
ztxai/
├── run.py                 # entry point
├── config.py               # env-based configuration
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py         # app factory
│   ├── extensions.py       # db, login_manager
│   ├── models.py           # User, LoginEvent, EvidenceLog
│   ├── routes/
│   │   ├── auth.py         # register/login/logout + log_login_event()
│   │   └── dashboard.py
│   ├── templates/
│   └── static/
├── ml/                      # Steps 4-7 will live here
├── forensics/                # Step 11 will live here
└── data/                     # synthetic + UNSW-NB15/CIC-IDS CSVs
```
