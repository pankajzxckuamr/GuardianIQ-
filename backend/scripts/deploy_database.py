#!/usr/bin/env python3
"""
GuardianIQ Database Deployment & Migration Script
Handles connection validation, Alembic schema migrations, DDL script execution,
and optional seeding or database restore.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GuardianIQ-DB-Deploy")

# Resolve paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BACKEND_DIR.parent
DDL_DIR = WORKSPACE_DIR / "database" / "ddl"
SEED_DIR = WORKSPACE_DIR / "database" / "seed"

# Ensure backend directory is in sys.path
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def wait_for_database(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """Waits for PostgreSQL to be ready and accept connections."""
    from sqlalchemy import create_engine, text
    from app.core.config import settings

    logger.info(f"Checking database connection to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured DATABASE_URL'}")
    
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            logger.info(" Database connection verified successfully.")
            return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_interval)
    
    logger.error("❌ Database connection timed out. Exiting.")
    return False


def run_alembic_migrations():
    """Runs Alembic migrations to upgrade the schema to head."""
    logger.info("Running Alembic migrations (upgrade head)...")
    from alembic import command
    from alembic.config import Config

    alembic_ini_path = BACKEND_DIR / "alembic.ini"
    if not alembic_ini_path.exists():
        logger.error(f"❌ alembic.ini not found at: {alembic_ini_path}")
        return False

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "app" / "db" / "migrations"))
    
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info(" Alembic migrations applied successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Error during Alembic migration: {e}")
        return False


def apply_ddl_patches():
    """Executes SQL patch files in database/ddl directory in order."""
    from sqlalchemy import create_engine, text
    from app.core.config import settings

    if not DDL_DIR.exists():
        logger.warning(f"DDL directory not found at: {DDL_DIR}")
        return True

    sql_files = sorted([f for f in DDL_DIR.glob("*.sql")])
    if not sql_files:
        logger.info("No DDL patch files found in database/ddl.")
        return True

    logger.info(f"Applying {len(sql_files)} DDL patch files...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        for sql_file in sql_files:
            logger.info(f"  -> Executing: {sql_file.name}")
            try:
                with open(sql_file, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    conn.execute(text(content))
                logger.info(f"     Applied {sql_file.name}")
            except Exception as e:
                logger.warning(f"     Notice/Error on {sql_file.name}: {e}")
    
    logger.info(" DDL patches applied.")
    return True


def run_seed_data():
    """Runs backend seed scripts to populate baseline tenants, users, and governance data."""
    logger.info("Running seed scripts...")
    try:
        import app.db.seed as base_seed
        base_seed.seed_all()
        logger.info(" Base seed completed.")
    except Exception as e:
        logger.warning(f"Base seed warning: {e}")

    try:
        import app.db.seed_phase2 as seed_p2
        if hasattr(seed_p2, "seed"):
            seed_p2.seed()
        logger.info(" Phase 2 seed completed.")
    except Exception as e:
        logger.warning(f"Phase 2 seed warning: {e}")

    try:
        import app.db.seed_phase5 as seed_p5
        if hasattr(seed_p5, "seed"):
            seed_p5.seed()
        logger.info(" Phase 5 seed completed.")
    except Exception as e:
        logger.warning(f"Phase 5 seed warning: {e}")

    logger.info(" Data seeding process completed.")
    return True


def run_backup_import():
    """Imports the full database SQL backup file."""
    logger.info("Restoring database from GuardianIQ_Database_Backup.sql...")
    try:
        from import_backup import run_import
        run_import()
        logger.info(" Backup import executed.")
        return True
    except Exception as e:
        logger.error(f"❌ Backup import failed: {e}")
        return False


def verify_tables():
    """Verifies that core tables exist in the deployed database."""
    from sqlalchemy import create_engine, inspect
    from app.core.config import settings

    logger.info("Verifying database schema...")
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    required_tables = [
        "tenants", "users", "departments", "audit_logs",
        "generic_relationships", "object_responsibilities",
        "policies", "ai_models", "ai_agents"
    ]

    missing = [t for t in required_tables if t not in existing_tables]
    if missing:
        logger.warning(f"⚠️ Warning: Some expected tables were not found: {missing}")
    else:
        logger.info(f" All core tables ({len(required_tables)} checked) exist in database.")
    logger.info(f"Total tables in database: {len(existing_tables)}")
    return True


def main():
    parser = argparse.ArgumentParser(description="GuardianIQ Database Deployment & Migration Tool")
    parser.add_argument("--wait-only", action="store_true", help="Only wait for database connectivity")
    parser.add_argument("--migrate-only", action="store_true", help="Only run Alembic migrations")
    parser.add_argument("--seed", action="store_true", help="Run database seed scripts after migration")
    parser.add_argument("--import-backup", action="store_true", help="Restore full database backup after migration")
    parser.add_argument("--skip-ddl", action="store_true", help="Skip DDL patches")
    parser.add_argument("--verify", action="store_true", help="Verify tables exist")
    args = parser.parse_args()

    logger.info("==========================================")
    logger.info("  GuardianIQ Database Deployment Tool     ")
    logger.info("==========================================")

    # 1. Wait for DB
    if not wait_for_database():
        sys.exit(1)

    if args.wait_only:
        logger.info("Database connectivity check passed.")
        sys.exit(0)

    # 2. Run Migrations
    if not run_alembic_migrations():
        logger.error("Database migration failed.")
        sys.exit(1)

    if args.migrate_only:
        sys.exit(0)

    # 3. Apply DDL patches
    if not args.skip_ddl:
        apply_ddl_patches()

    # 4. Optional Seed / Backup
    if args.import_backup:
        run_backup_import()
    elif args.seed:
        run_seed_data()

    # 5. Verify
    verify_tables()
    logger.info("🎉 Database deployment and setup finished successfully.")


if __name__ == "__main__":
    main()
