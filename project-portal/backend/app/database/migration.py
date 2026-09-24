"""Automatic schema migration module for Hogwarts Legacy 5.0.

Ensures that required columns exist across all environments (PostgreSQL Neon, SQLite, etc.)
without requiring manual migration scripts to be triggered separately.
"""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def auto_migrate_schema(engine: Engine) -> None:
    """Safely apply schema additions and new columns to existing database tables."""
    from app.database.base import Base
    import app.models  # noqa: F401

    # 1. Ensure all base tables exist
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Base.metadata.create_all notice: %s", e)

    # 2. Check and add missing columns to users table
    dialect_name = engine.dialect.name.lower()
    is_postgres = "postgres" in dialect_name

    bool_type = "BOOLEAN DEFAULT FALSE"
    text_type = "TEXT"
    dt_type = "TIMESTAMP WITH TIME ZONE" if is_postgres else "DATETIME"

    user_columns = [
        ("edit_permission", bool_type),
        ("edit_permission_reason", text_type),
        ("edit_permission_granted_at", dt_type),
        ("session_last_active", dt_type),
        ("password_reset_required", bool_type),
    ]

    project_columns = [
        ("assigned_problem_statement_id", "INTEGER"),
        ("draft_saved_at", dt_type),
        ("submitted_at", dt_type),
        ("technology_stack", text_type),
    ]

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Inspect existing columns to avoid unnecessary DDL errors
            inspector = inspect(engine)
            existing_user_cols = set()
            existing_project_cols = set()

            if inspector.has_table("users"):
                existing_user_cols = {col["name"].lower() for col in inspector.get_columns("users")}
            if inspector.has_table("projects"):
                existing_project_cols = {col["name"].lower() for col in inspector.get_columns("projects")}

            # Add missing user columns
            for col_name, col_def in user_columns:
                if col_name.lower() not in existing_user_cols:
                    try:
                        if is_postgres:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))
                        else:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"))
                        print(f"  [MIGRATION] Added column users.{col_name}")
                    except Exception as ex:
                        print(f"  [MIGRATION] Column users.{col_name} note: {ex}")

            # Add missing project columns
            for col_name, col_def in project_columns:
                if col_name.lower() not in existing_project_cols:
                    try:
                        if is_postgres:
                            conn.execute(text(f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))
                        else:
                            conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def};"))
                        print(f"  [MIGRATION] Added column projects.{col_name}")
                    except Exception as ex:
                        print(f"  [MIGRATION] Column projects.{col_name} note: {ex}")

            # Clean default null values
            try:
                conn.execute(text("UPDATE users SET edit_permission = FALSE WHERE edit_permission IS NULL;"))
                conn.execute(text("UPDATE users SET password_reset_required = FALSE WHERE password_reset_required IS NULL;"))
            except Exception:
                pass

            trans.commit()
            print("  [MIGRATION] Database schema migration successfully verified.")
        except Exception as e:
            trans.rollback()
            logger.error("Auto schema migration error: %s", e)
            print(f"  [MIGRATION ERROR] {e}")
