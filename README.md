# Project Portal — Full Stack Application

A FastAPI + PostgreSQL + Vanilla JS project submission and review portal with domain-based problem statement assignment.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT Auth
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: PythonAnywhere

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Node.js (optional, for `serve`)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Mahesh6885/Hogward_Backend.git
cd Hogward_Backend/project-portal/backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure .env
cp .env.example .env
# Edit .env with your local PostgreSQL credentials

# 5. Run database migrations
alembic upgrade head

# 6. Seed the database
python seed.py

# 7. Start the backend
uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend — in a separate terminal
npx serve ../frontend -l 5500
# Open http://localhost:5500
```

### Default Credentials (after seed.py)
| Role  | Username   | Password            |
|-------|------------|---------------------|
| Admin | admin      | change-this-password |
| User  | alice_ai   | UserPassword123!    |
| User  | bob_cyber  | UserPassword123!    |
| User  | carol_oi   | UserPassword123!    |

---

## PythonAnywhere Deployment

See [`DEPLOY.md`](DEPLOY.md) for full step-by-step instructions.
