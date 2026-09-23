"""
WSGI entry point for PythonAnywhere.

Place this file path in your PythonAnywhere Web App config:
  Source code:     /home/YOUR_PA_USER/Hogward_Backend/project-portal/backend
  Working directory: /home/YOUR_PA_USER/Hogward_Backend/project-portal/backend
  WSGI file:       /home/YOUR_PA_USER/Hogward_Backend/project-portal/backend/wsgi.py
  Virtualenv:      /home/YOUR_PA_USER/Hogward_Backend/project-portal/backend/venv
"""

import sys
import os

# Add the backend directory to the Python path and change working directory
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
os.chdir(project_dir)

# Load .env variables before importing the app
from dotenv import load_dotenv
load_dotenv(os.path.join(project_dir, '.env'))

# Import the FastAPI app and wrap with ASGI middleware for WSGI compatibility
from app.main import app

# PythonAnywhere uses WSGI; wrap FastAPI (ASGI) with a2wsgi
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)
