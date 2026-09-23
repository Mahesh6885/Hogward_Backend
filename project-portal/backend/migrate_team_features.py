"""Database migration script for team-based dashboard enhancement."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.database import engine

def run_migration():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Running database migrations...")
            
            # 1. users table columns
            user_columns = [
                ("team_name", "VARCHAR(255)"),
                ("team_leader", "VARCHAR(255)"),
                ("member_one", "VARCHAR(255)"),
                ("member_two", "VARCHAR(255)"),
                ("member_three", "VARCHAR(255)"),
                ("member_four", "VARCHAR(255)"),
                ("college_name", "VARCHAR(255)"),
                ("department", "VARCHAR(255)"),
                ("academic_year", "VARCHAR(50)"),
            ]
            for col_name, col_type in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"  [OK] Checked column users.{col_name}")

            # Populate team_name, team_leader, college_name for existing users if NULL
            conn.execute(text("""
                UPDATE users
                SET team_name = COALESCE(team_name, name),
                    team_leader = COALESCE(team_leader, name),
                    college_name = COALESCE(college_name, organization)
                WHERE team_name IS NULL OR team_leader IS NULL OR college_name IS NULL;
            """))

            # 2. projects table columns
            project_columns = [
                ("project_title", "VARCHAR(255)"),
                ("abstract", "TEXT"),
                ("problem_statement", "TEXT"),
                ("objectives", "TEXT"),
                ("proposed_solution", "TEXT"),
                ("technologies", "TEXT"),
                ("expected_outcome", "TEXT"),
                ("project_description", "TEXT"),
                ("github_url", "VARCHAR(500)"),
                ("demo_url", "VARCHAR(500)"),
            ]
            for col_name, col_type in project_columns:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"  [OK] Checked column projects.{col_name}")

            # Populate project_title from custom_topic or topic title if NULL
            conn.execute(text("""
                UPDATE projects p
                SET project_title = COALESCE(
                    p.project_title,
                    p.custom_topic,
                    (SELECT t.title FROM topics t WHERE t.id = p.topic_id),
                    'Project ' || p.project_code
                )
                WHERE p.project_title IS NULL;
            """))

            # 3. reviews table columns
            conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS suggested_improvements TEXT;"))
            print("  [OK] Checked column reviews.suggested_improvements")

            # 4. team_topic_locks table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS team_topic_locks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT uq_team_topic_lock UNIQUE (user_id, topic_id)
                );
            """))
            print("  [OK] Checked table team_topic_locks")

            trans.commit()
            print("[SUCCESS] All database migrations applied successfully!")
        except Exception as e:
            trans.rollback()
            print(f"[ERROR] Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration()
