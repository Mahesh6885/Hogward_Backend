"""Database migration script for Hogwarts Legacy 5.0 — Edit Permission & Session Security."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.database import engine

def run_migration():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Applying Hogwarts Legacy 5.0 database migrations...")

            # 1. users table columns
            columns_to_add = [
                ("edit_permission", "BOOLEAN DEFAULT FALSE"),
                ("edit_permission_reason", "TEXT"),
                ("edit_permission_granted_at", "TIMESTAMP WITH TIME ZONE"),
                ("session_last_active", "TIMESTAMP WITH TIME ZONE"),
                ("password_reset_required", "BOOLEAN DEFAULT FALSE"),
            ]

            for col_name, col_def in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))
                    print(f"  [OK] Checked/added column users.{col_name}")
                except Exception as ex:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"))
                        print(f"  [OK] Added column users.{col_name}")
                    except Exception as ex2:
                        print(f"  [INFO] Column users.{col_name} already exists or handled ({ex2})")

            # Update existing rows so edit_permission is False and password_reset_required is False
            try:
                conn.execute(text("UPDATE users SET edit_permission = FALSE WHERE edit_permission IS NULL;"))
                conn.execute(text("UPDATE users SET password_reset_required = FALSE WHERE password_reset_required IS NULL;"))
            except Exception as e:
                print(f"  [INFO] Update defaults note: {e}")

            trans.commit()
            print("[SUCCESS] Hogwarts Legacy 5.0 migrations applied successfully!")
        except Exception as e:
            trans.rollback()
            print(f"[ERROR] Migration failed: {e}")
            raise

if __name__ == "__main__":
    run_migration()
