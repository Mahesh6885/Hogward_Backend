# PythonAnywhere Deployment Guide — Project Portal (MySQL)

This guide walks you through deploying Project Portal on **PythonAnywhere** using their built-in **free MySQL database**.

---

## Step 1 — Create Your MySQL Database on PythonAnywhere

1. Log in to [PythonAnywhere](https://www.pythonanywhere.com/).
2. Go to the **Databases** tab in your dashboard.
3. If you haven't set a MySQL password yet, enter a password in the **Set database password** box and save it.
4. Under **Create database**, enter:
   ```
   project_portal
   ```
   and click **Create database**.
5. Note your database details shown on the page:
   - **Database Host**: `YOUR_USERNAME.mysql.pythonanywhere-services.com`
   - **Database Name**: `YOUR_USERNAME$project_portal`
   - **Username**: `YOUR_USERNAME`
   - **Password**: *(The MySQL password you set above)*

---

## Step 2 — Open a Bash Console on PythonAnywhere

1. Go to **Dashboard → Consoles → Bash**.
2. Run the following commands:

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/Mahesh6885/Hogward_Backend.git

# Move into the backend directory
cd Hogward_Backend/project-portal/backend

# Create a virtual environment using Python 3.10
python3.10 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install all backend dependencies (includes PyMySQL, cryptography, a2wsgi, FastAPI)
pip install --upgrade pip
pip install -r requirements.txt
```

*(If you had previously cloned the repo, simply run `cd ~/Hogward_Backend && git pull` and activate your venv).*

---

## Step 3 — Create and Configure `.env` File

Inside `~/Hogward_Backend/project-portal/backend/`:

```bash
cp .env.example .env
nano .env
```

Set your configuration values (replace `YOUR_USERNAME` and `YOUR_MYSQL_PASSWORD`):

```env
APP_NAME=Project Portal
APP_ENV=production

# PythonAnywhere MySQL Connection String:
DATABASE_URL=mysql+pymysql://YOUR_USERNAME:YOUR_MYSQL_PASSWORD@YOUR_USERNAME.mysql.pythonanywhere-services.com/YOUR_USERNAME$project_portal

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

## Step 4 — Initialize MySQL Database & Seed Data

With the virtual environment activated:

```bash
# Inside ~/Hogward_Backend/project-portal/backend with (venv) active:
python seed.py
```

This single command automatically:
1. Creates all tables in your MySQL database (`domains`, `users`, `problem_statements`, `projects`, `reviews`, `audit_logs`).
2. Seeds domains (`AI`, `CYBERSECURITY`, `OPEN_INNOVATION`).
3. Seeds the **10 predefined AI problem statements** and **10 predefined Cybersecurity problem statements**.
4. Creates the default admin user.
5. Seeds sample users & projects.

---

## Step 5 — Configure Web App in PythonAnywhere

1. Go to PythonAnywhere **Dashboard → Web**.
2. If you don't have a web app yet:
   - Click **Add a new web app**
   - Click **Next** → Select **Manual configuration** → Select **Python 3.10** → Click **Next**
3. In the Web App configuration page:

| Section | Setting | Path |
|---|---|---|
| **Code** | **Source code** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend` |
| **Code** | **Working directory** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend` |
| **Virtualenv** | **Virtualenv** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend/venv` |

---

## Step 6 — Configure WSGI File

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

## Step 7 — Configure Static Files (Frontend)

On the **Web** tab, scroll down to the **Static files** section and add:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/frontend` |

---

## Step 8 — Reload and Visit

1. Click the big green **"Reload <YOUR_USERNAME>.pythonanywhere.com"** button at the top of the **Web** tab.
2. Your app is now live!
   - **Frontend**: `https://YOUR_USERNAME.pythonanywhere.com/static/index.html`
   - **Interactive API Docs**: `https://YOUR_USERNAME.pythonanywhere.com/docs`
   - **API Health**: `https://YOUR_USERNAME.pythonanywhere.com/health`

---

## Future Updates

Whenever you make updates on local or push to GitHub:

```bash
cd ~/Hogward_Backend
git pull
# If new packages were added:
source project-portal/backend/venv/bin/activate
pip install -r project-portal/backend/requirements.txt
```
Then click the **Reload** button in the **Web** tab.
