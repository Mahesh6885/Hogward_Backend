# PythonAnywhere Deployment Guide — Project Portal (SQLite)

This guide walks you through deploying Project Portal on **PythonAnywhere** using **SQLite**.

> 💡 **Why SQLite?**
> - **100% Free** — No paid database add-ons needed.
> - **Zero Configuration** — No database server setup, no database passwords.
> - **Zero Network Issues** — Runs locally as a file directly in your backend directory, bypassing PythonAnywhere's free tier proxy restrictions.

---

## Step 1 — Open a Bash Console on PythonAnywhere

1. Log in to [PythonAnywhere](https://www.pythonanywhere.com/).
2. Go to **Dashboard → Consoles → Bash**.
3. Run the following commands:

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/Mahesh6885/Hogward_Backend.git

# Move into the backend directory
cd Hogward_Backend/project-portal/backend

# (If you had cloned previously, just update the code):
# cd ~/Hogward_Backend && git pull && cd project-portal/backend

# Create a virtual environment using Python 3.10
python3.10 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install all backend dependencies (FastAPI, a2wsgi, SQLAlchemy, etc.)
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 2 — Create and Configure `.env` File

Still inside `~/Hogward_Backend/project-portal/backend/` in the Bash console:

```bash
cp .env.example .env
nano .env
```

Set your configuration values (replace `YOUR_USERNAME` with your actual PythonAnywhere username):

```env
APP_NAME=Project Portal
APP_ENV=production

# SQLite database file path (absolute path):
DATABASE_URL=sqlite:////home/YOUR_USERNAME/Hogward_Backend/project-portal/backend/project_portal.db

JWT_SECRET_KEY=e83a9f018e69d7b43c683b54784a9238e811c750ba42c16f81a7b8e1a123
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

CORS_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com,http://localhost:5500,http://127.0.0.1:5500

MAX_REVIEW_ROUNDS=3

ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-this-password
ADMIN_NAME=System Administrator
```

> **To save in nano**: Press `Ctrl+O` → `Enter` → `Ctrl+X`.

---

## Step 3 — Initialize Database & Seed Data

With the virtual environment active (`source venv/bin/activate`):

```bash
# Inside ~/Hogward_Backend/project-portal/backend:
python seed.py
```

This single command automatically:
1. Creates the `project_portal.db` SQLite file with all database tables (`domains`, `users`, `problem_statements`, `projects`, `reviews`, `audit_logs`).
2. Seeds domains (`AI`, `CYBERSECURITY`, `OPEN_INNOVATION`).
3. Seeds all **10 AI** and **10 Cybersecurity** problem statements.
4. Creates your admin account (`admin` / `change-this-password`).
5. Seeds sample users & projects.

---

## Step 4 — Configure Web App in PythonAnywhere

1. Go to PythonAnywhere **Dashboard → Web**.
2. If you don't have a web app yet:
   - Click **Add a new web app**
   - Click **Next** → Select **Manual configuration (including virtualenvs)** → Select **Python 3.10** → Click **Next**
3. In the Web App configuration page, set:

| Section | Setting | Path |
|---|---|---|
| **Code** | **Source code** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend` |
| **Code** | **Working directory** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend` |
| **Virtualenv** | **Virtualenv** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend/venv` |

---

## Step 5 — Configure WSGI File

1. On the **Web** tab, click the link next to **WSGI configuration file** (e.g. `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`).
2. **Clear out everything** in the file and replace it with:

```python
import sys
import os

project_dir = '/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_dir, '.env'))

from app.main import app
from a2wsgi import ASGIMiddleware

application = ASGIMiddleware(app)
```

*(Make sure to change `YOUR_USERNAME` to your actual PythonAnywhere username).*
3. Click the **Save** button in the top right.

---

## Step 6 — Configure Static Files (Frontend)

On the **Web** tab, scroll down to the **Static files** section and add:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/frontend` |

---

## Step 7 — Reload and Visit

1. Click the big green **"Reload <YOUR_USERNAME>.pythonanywhere.com"** button at the top of the **Web** tab.
2. Your app is now live!
   - **Frontend App**: `https://YOUR_USERNAME.pythonanywhere.com/static/index.html`
   - **Interactive API Docs**: `https://YOUR_USERNAME.pythonanywhere.com/docs`
   - **Health Check**: `https://YOUR_USERNAME.pythonanywhere.com/health`

---

## Future Updates

Whenever you make updates on local or push to GitHub:

```bash
cd ~/Hogward_Backend
git pull
# If you changed dependencies:
source project-portal/backend/venv/bin/activate
pip install -r project-portal/backend/requirements.txt
```
Then click the **Reload** button in the **Web** tab.
