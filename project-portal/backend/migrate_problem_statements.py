"""Database migration script for problem statements."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.database import engine

def run_migration():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Creating problem_statements table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS problem_statements (
                    id SERIAL PRIMARY KEY,
                    problem_code VARCHAR(20) NOT NULL UNIQUE,
                    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE RESTRICT,
                    detailed_description TEXT NOT NULL,
                    is_assigned BOOLEAN NOT NULL DEFAULT FALSE,
                    assigned_team_id INTEGER NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_problem_statements_id ON problem_statements(id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_problem_statements_problem_code ON problem_statements(problem_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_problem_statements_domain_id ON problem_statements(domain_id);"))
            print("  [OK] problem_statements table & indexes ready.")

            print("Adding assigned_problem_statement_id column to projects...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS assigned_problem_statement_id INTEGER REFERENCES problem_statements(id) ON DELETE SET NULL;
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_assigned_problem_statement_id ON projects(assigned_problem_statement_id);"))
            print("  [OK] projects.assigned_problem_statement_id ready.")

            trans.commit()
            print("Problem statements migration completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration()
