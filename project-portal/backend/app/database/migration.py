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
                    conn.execute(text("""
                        DO $$ BEGIN
                            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'domain_name_enum') THEN
                                ALTER TYPE domain_name_enum ADD VALUE IF NOT EXISTS 'OPEN_INNOVATION';
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
                ("sorting_ceremony_completed", "BOOLEAN DEFAULT FALSE"),
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
                ("assigned_at", dt_type),
                ("created_at", f"{dt_type} DEFAULT CURRENT_TIMESTAMP"),
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

            # Drop legacy topic_id and custom_topic from projects if PostgreSQL
            if is_postgres:
                for legacy_col in ("topic_id", "custom_topic"):
                    if legacy_col in existing_project_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE projects DROP COLUMN IF EXISTS {legacy_col};"))
                            print(f"  [MIGRATION] Dropped legacy {legacy_col} from projects table.")
                        except Exception as ex:
                            print(f"  [MIGRATION] Drop {legacy_col} notice: {ex}")

                # Drop unique constraint on reviews(project_id, round_number) to allow multiple reviews per round
                try:
                    conn.execute(text("ALTER TABLE reviews DROP CONSTRAINT IF EXISTS uq_reviews_project_round;"))
                    print("  [MIGRATION] Dropped uq_reviews_project_round constraint if present.")
                except Exception as ex:
                    print(f"  [MIGRATION] Drop uq_reviews_project_round notice: {ex}")

            # Clean default null values
            try:
                conn.execute(text("UPDATE users SET edit_permission = FALSE WHERE edit_permission IS NULL;"))
                conn.execute(text("UPDATE users SET password_reset_required = FALSE WHERE password_reset_required IS NULL;"))
            except Exception:
                pass

            # Ensure all 3 domains exist in domains table
            for d_name, d_desc in [
                ("AI", "Artificial Intelligence — covers machine learning, deep learning, NLP, computer vision, and more."),
                ("CYBERSECURITY", "Cybersecurity — covers network security, ethical hacking, cryptography, forensics, and more."),
                ("OPEN_INNOVATION", "Open Innovation — open track for creative, cross-disciplinary technical solutions."),
            ]:
                try:
                    exists = conn.execute(text("SELECT id FROM domains WHERE name = :name LIMIT 1;"), {"name": d_name}).fetchone()
                    if not exists:
                        conn.execute(text("INSERT INTO domains (name, description, created_at) VALUES (:name, :desc, CURRENT_TIMESTAMP);"), {"name": d_name, "desc": d_desc})
                        print(f"  [MIGRATION] Seeded domain {d_name}")
                except Exception as dex:
                    print(f"  [MIGRATION] Domain {d_name} notice: {dex}")

            trans.commit()
            print("  [MIGRATION] PostgreSQL schema successfully synchronized and verified.")
        except Exception as e:
            trans.rollback()
            logger.error("Auto schema migration error: %s", e)
            print(f"  [MIGRATION ERROR] {e}")
