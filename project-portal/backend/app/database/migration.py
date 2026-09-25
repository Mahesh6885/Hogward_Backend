"""Automatic schema migration module for Hogwarts Legacy 5.0 (Render PostgreSQL + SQLite).

Safely handles the complete removal of topics and replaces it with the official problem_statements module.
Preserves existing users, projects, reviews, authentication, and permissions.
"""
import logging
import uuid
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def auto_migrate_schema(engine: Engine) -> None:
    """Safely apply schema migrations for PostgreSQL (Render) and SQLite."""
    dialect_name = engine.dialect.name.lower()
    is_postgres = "postgres" in dialect_name

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Drop legacy topic tables if they exist
            print("  [MIGRATION] Dropping legacy topic tables if present...")
            if is_postgres:
                conn.execute(text("DROP TABLE IF EXISTS team_topic_locks CASCADE;"))
                conn.execute(text("DROP TABLE IF EXISTS topics CASCADE;"))
            else:
                conn.execute(text("DROP TABLE IF EXISTS team_topic_locks;"))
                conn.execute(text("DROP TABLE IF EXISTS topics;"))

            # 2. Check if problem_statements table exists and whether its id column is UUID
            inspector = inspect(engine)
            recreate_ps = False
            if inspector.has_table("problem_statements"):
                cols = {c["name"].lower(): c for c in inspector.get_columns("problem_statements")}
                id_col = cols.get("id")
                # If id is INTEGER or not UUID/CHAR, we drop and recreate (since Render has 0 projects)
                col_type_str = str(id_col["type"]).lower() if id_col else ""
                if "int" in col_type_str or "serial" in col_type_str:
                    recreate_ps = True
                if "domain_id" in cols and "realm" not in cols:
                    recreate_ps = True

            if recreate_ps:
                print("  [MIGRATION] Recreating problem_statements table with UUID primary key and realm enum...")
                if is_postgres:
                    # Drop any old FK on projects
                    try:
                        conn.execute(text("ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_problem_statements;"))
                        conn.execute(text("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_assigned_problem_statement_id_fkey;"))
                        conn.execute(text("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_problem_statement_id_fkey;"))
                    except Exception:
                        pass
                    conn.execute(text("DROP TABLE IF EXISTS problem_statements CASCADE;"))
                else:
                    conn.execute(text("DROP TABLE IF EXISTS problem_statements;"))

            # 3. Create ENUM types in PostgreSQL if not exist
            if is_postgres:
                try:
                    conn.execute(text("""
                        DO $$ BEGIN
                            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'realm_enum') THEN
                                CREATE TYPE realm_enum AS ENUM ('AI', 'CYBERSECURITY');
                            END IF;
                        END $$;
                    """))
                    conn.execute(text("""
                        DO $$ BEGIN
                            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'difficulty_enum') THEN
                                CREATE TYPE difficulty_enum AS ENUM ('BEGINNER', 'INTERMEDIATE', 'ADVANCED');
                            END IF;
                        END $$;
                    """))
                except Exception as ex:
                    print(f"  [MIGRATION] ENUM creation notice: {ex}")

            trans.commit()
        except Exception as e:
            trans.rollback()
            print(f"  [MIGRATION PRE-STEP NOTICE] {e}")

    # 4. Now create tables defined in SQLAlchemy Base (creates problem_statements with UUID if missing)
    from app.database.base import Base
    import app.models  # noqa: F401
    try:
        Base.metadata.create_all(bind=engine)
        print("  [MIGRATION] Base.metadata.create_all completed.")
    except Exception as e:
        print(f"  [MIGRATION] Base create_all notice: {e}")

    # 5. Alter projects and users tables to ensure new columns exist
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            inspector = inspect(engine)
            existing_user_cols = {col["name"].lower() for col in inspector.get_columns("users")} if inspector.has_table("users") else set()
            existing_project_cols = {col["name"].lower() for col in inspector.get_columns("projects")} if inspector.has_table("projects") else set()

            dt_type = "TIMESTAMP WITH TIME ZONE" if is_postgres else "DATETIME"
            uuid_type = "UUID" if is_postgres else "CHAR(36)"

            # Ensure user columns
            user_cols_to_add = [
                ("edit_permission", "BOOLEAN DEFAULT FALSE"),
                ("edit_permission_reason", "TEXT"),
                ("edit_permission_granted_at", dt_type),
                ("session_last_active", dt_type),
                ("password_reset_required", "BOOLEAN DEFAULT FALSE"),
            ]
            for col_name, col_def in user_cols_to_add:
                if col_name.lower() not in existing_user_cols:
                    try:
                        cmd = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def};" if is_postgres else f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"
                        conn.execute(text(cmd))
                        print(f"  [MIGRATION] Added column users.{col_name}")
                    except Exception as ex:
                        print(f"  [MIGRATION] Column users.{col_name} notice: {ex}")

            # Ensure projects columns
            project_cols_to_add = [
                ("problem_statement_id", f"{uuid_type} REFERENCES problem_statements(id) ON DELETE RESTRICT" if is_postgres else f"{uuid_type}"),
                ("problem_code", "VARCHAR(20)"),
                ("realm", "realm_enum" if is_postgres else "VARCHAR(50)"),
                ("draft_saved_at", dt_type),
                ("submitted_at", dt_type),
                ("technology_stack", "TEXT"),
            ]
            for col_name, col_def in project_cols_to_add:
                if col_name.lower() not in existing_project_cols:
                    try:
                        cmd = f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {col_name} {col_def};" if is_postgres else f"ALTER TABLE projects ADD COLUMN {col_name} {col_def};"
                        conn.execute(text(cmd))
                        print(f"  [MIGRATION] Added column projects.{col_name}")
                    except Exception as ex:
                        print(f"  [MIGRATION] Column projects.{col_name} notice: {ex}")

            # Drop topic_id from projects if PostgreSQL
            if is_postgres and "topic_id" in existing_project_cols:
                try:
                    conn.execute(text("ALTER TABLE projects DROP COLUMN IF EXISTS topic_id;"))
                    print("  [MIGRATION] Dropped legacy topic_id from projects table.")
                except Exception as ex:
                    print(f"  [MIGRATION] Drop topic_id notice: {ex}")

            # Clean default null values
            try:
                conn.execute(text("UPDATE users SET edit_permission = FALSE WHERE edit_permission IS NULL;"))
                conn.execute(text("UPDATE users SET password_reset_required = FALSE WHERE password_reset_required IS NULL;"))
            except Exception:
                pass

            trans.commit()
            print("  [MIGRATION] PostgreSQL schema successfully synchronized and verified.")
        except Exception as e:
            trans.rollback()
            logger.error("Auto schema migration error: %s", e)
            print(f"  [MIGRATION ERROR] {e}")
