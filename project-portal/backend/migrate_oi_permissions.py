"""Migration script to add allow_problem_statement_edit column to users table
and set default status on projects to 'DRAFT'.
Preserves all registered teams, projects, problem statements, and review data.
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('D:/Hogward_backend/project-portal/backend/.env')
sys.path.insert(0, 'D:/Hogward_backend/project-portal/backend')

from app.database.database import engine
from sqlalchemy import text, inspect

def run_migration():
    print("[MIGRATION] Starting Open Innovation & Edit Permission migration...")
    dialect_name = engine.dialect.name.lower()
    is_postgres = "postgres" in dialect_name

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Add allow_problem_statement_edit to users
            inspector = inspect(engine)
            user_cols = {c["name"].lower() for c in inspector.get_columns("users")}
            if "allow_problem_statement_edit" not in user_cols:
                if is_postgres:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS allow_problem_statement_edit BOOLEAN DEFAULT FALSE;"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN allow_problem_statement_edit BOOLEAN DEFAULT 0;"))
                print("  [OK] Added allow_problem_statement_edit column to users")
            else:
                print("  [INFO] users.allow_problem_statement_edit already exists")

            # 2. Ensure existing nulls are False
            conn.execute(text("UPDATE users SET allow_problem_statement_edit = FALSE WHERE allow_problem_statement_edit IS NULL;"))
            print("  [OK] Sanitized users.allow_problem_statement_edit")

            # 3. Update default for projects.status to DRAFT
            if is_postgres:
                conn.execute(text("ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'DRAFT';"))
                print("  [OK] Set default projects.status to 'DRAFT'")

            trans.commit()
            print("[MIGRATION SUCCESS] Migration finished successfully!")
        except Exception as e:
            trans.rollback()
            print(f"[MIGRATION ERROR] {e}")
            raise

if __name__ == "__main__":
    run_migration()
