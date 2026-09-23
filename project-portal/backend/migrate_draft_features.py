"""Migration script to add DRAFT status, technology_stack, is_submitted, draft_saved_at."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.database import engine

def run_migration():
    print("Starting draft features migration...")
    
    # In PostgreSQL, ALTER TYPE ... ADD VALUE cannot run inside an active transaction block.
    # We execute it on a connection in AUTOCOMMIT mode.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        try:
            # Check existing enum values
            enums = conn.execute(text("SELECT enumlabel FROM pg_enum WHERE enumtypid = 'project_status_enum'::regtype")).fetchall()
            existing_labels = [e[0] for e in enums]
            if "DRAFT" not in existing_labels:
                conn.execute(text("ALTER TYPE project_status_enum ADD VALUE 'DRAFT';"))
                print("  [OK] Added 'DRAFT' to project_status_enum")
            else:
                print("  [OK] 'DRAFT' already exists in project_status_enum")
        except Exception as e:
            print(f"  [NOTE] Enum check/update: {e}")

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Add technology_stack column
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS technology_stack TEXT;"))
            print("  [OK] Checked column projects.technology_stack")

            # Sync technology_stack from technologies if NULL
            conn.execute(text("UPDATE projects SET technology_stack = technologies WHERE technology_stack IS NULL AND technologies IS NOT NULL;"))

            # 2. Add is_submitted column
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_submitted BOOLEAN DEFAULT FALSE;"))
            print("  [OK] Checked column projects.is_submitted")

            # Existing submitted projects get is_submitted = TRUE
            conn.execute(text("UPDATE projects SET is_submitted = TRUE WHERE status != 'DRAFT';"))

            # 3. Add draft_saved_at column
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS draft_saved_at TIMESTAMP WITH TIME ZONE;"))
            print("  [OK] Checked column projects.draft_saved_at")

            # 4. Make submitted_at nullable
            conn.execute(text("ALTER TABLE projects ALTER COLUMN submitted_at DROP NOT NULL;"))
            print("  [OK] Made projects.submitted_at nullable")

            trans.commit()
            print("[SUCCESS] Draft features migration applied successfully!")
        except Exception as e:
            trans.rollback()
            print(f"[ERROR] Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration()
