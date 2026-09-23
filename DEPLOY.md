# PythonAnywhere Deployment Guide — Project Portal

## Prerequisites
- A [PythonAnywhere](https://www.pythonanywhere.com) account (free **Hacker** plan works)
- Your GitHub repo: `https://github.com/Mahesh6885/Hogward_Backend.git`

---

## Step 1 — Create a PostgreSQL Database

> ⚠️ **Note:** Free PythonAnywhere accounts only include **MySQL**, not PostgreSQL.  
> For PostgreSQL you need a **paid plan**, OR use a free external PostgreSQL service like:
> - [Neon](https://neon.tech) (free tier, recommended)
> - [Supabase](https://supabase.com) (free tier)
> - [ElephantSQL](https://www.elephantsql.com) (free tier)

### Option A — Use Neon (Free External PostgreSQL)
1. Go to [https://neon.tech](https://neon.tech) → Sign up → Create a project
2. Copy the **connection string** — it looks like:
   ```
   postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
3. Keep this for your `.env` file

### Option B — PythonAnywhere MySQL (Paid Only for PostgreSQL)
If on a paid plan, go to **Databases** tab → Create a PostgreSQL database.

---

## Step 2 — Open a Bash Console on PythonAnywhere

Go to **Dashboard → Consoles → Bash** and run:

```bash
# Clone your repository
git clone https://github.com/Mahesh6885/Hogward_Backend.git
cd Hogward_Backend/project-portal/backend

# Create a virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 3 — Create the .env File

```bash
# Inside: ~/Hogward_Backend/project-portal/backend/
cp .env.example .env
nano .env   # or: vi .env
```

Edit `.env` with your real values:
```env
APP_NAME=Project Portal
APP_ENV=production

# Use your Neon/Supabase connection string here:
DATABASE_URL=postgresql+psycopg://user:password@host/dbname?sslmode=require

JWT_SECRET_KEY=your-very-long-random-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Your PythonAnywhere domain:
CORS_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com

MAX_REVIEW_ROUNDS=3

ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=YourStrongAdminPassword123!
ADMIN_NAME=System Administrator
```

Save and exit (`Ctrl+X` → `Y` → Enter in nano).

---

## Step 4 — Run Database Migrations & Seed

```bash
# Still inside the backend directory with venv activated
cd ~/Hogward_Backend/project-portal/backend
source venv/bin/activate

# Run Alembic migrations to create all tables
alembic upgrade head

# Seed the database (creates domains, problem statements, admin account)
python seed.py
```

---

## Step 5 — Configure the Web App (WSGI)

1. Go to PythonAnywhere **Dashboard → Web → Add a new web app**
2. Choose **Manual configuration** (not Flask/Django)
3. Select **Python 3.11**

Then set these fields:

| Field | Value |
|-------|-------|
| **Source code** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend` |
| **Working directory** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend` |
| **Virtualenv** | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/backend/venv` |
| **WSGI file** | Click the link to edit (see below) |

### Edit the WSGI file
Click the WSGI configuration file link. **Replace everything** with:

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

> Replace `YOUR_USERNAME` with your actual PythonAnywhere username.

Save the WSGI file.

---

## Step 6 — Serve the Frontend as Static Files

1. In the **Web** tab, scroll down to **Static files**
2. Add an entry:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/Hogward_Backend/project-portal/frontend/` |

> This serves your HTML/CSS/JS files at `https://YOUR_USERNAME.pythonanywhere.com/static/`

---

## Step 7 — Update Frontend API Base URL

In your local code, update `project-portal/frontend/js/api.js` — the `BASE_URL` should point to your live backend:

```js
const BASE_URL = 'https://YOUR_USERNAME.pythonanywhere.com';
```

Then commit and push:
```bash
git add .
git commit -m "Update API base URL for production"
git push
```

On PythonAnywhere Bash, pull the update:
```bash
cd ~/Hogward_Backend
git pull
```

---

## Step 8 — Reload the Web App

Click the **Reload** button in the PythonAnywhere **Web** tab.

Your app is now live at:
- **API**: `https://YOUR_USERNAME.pythonanywhere.com/api/`
- **API Docs**: `https://YOUR_USERNAME.pythonanywhere.com/docs`
- **Frontend**: `https://YOUR_USERNAME.pythonanywhere.com/static/index.html`

---

## Step 9 — Future Updates (Pull & Reload)

Every time you push changes to GitHub:

```bash
# On PythonAnywhere Bash:
cd ~/Hogward_Backend
git pull
# Then click Reload in the Web tab
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure virtualenv path is correct in Web tab |
| `500 Internal Server Error` | Check error log in Web tab → **Error log** |
| DB connection error | Verify `DATABASE_URL` in `.env`, check if Neon allows connections |
| CORS error in browser | Add your PA domain to `CORS_ORIGINS` in `.env` |
| Static files not loading | Check the static files mapping in Web tab |
