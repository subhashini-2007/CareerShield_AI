"""CareerShield AI — Neon PostgreSQL Database Initialization & Verification Script.

Creates all database tables, verifies TLS/SSL connection health,
and checks schema tables without inserting unverified seed records.

Usage:
    cd backend
    python -m scripts.init_neon_db
    # Or:
    python scripts/init_neon_db.py
"""

import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import func, text
from app.core.config import settings
from app.core.database import SessionLocal, check_database_health, engine
from app.db.base import Base
from app.db.models import CompanyBenchmark, JobAnalysis


def initialize_database():
    """Verify connectivity and create tables for Neon PostgreSQL / local DB."""
    print("=" * 70)
    print("CareerShield AI — Database Initializer & Verification")
    print(f"Target Dialect: {settings.database_engine_name}")
    print(f"Environment:    {settings.APP_ENV}")
    print("=" * 70)

    # 1. Health check
    print("\n[1/3] Testing database connection...")
    health = check_database_health()
    if not health["connected"]:
        print(f"ERROR: Database connection failed: {health['error']}")
        sys.exit(1)

    print(f"SUCCESS: Connected to database in {health['latency_ms']}ms.")

    # 2. Inspect PostgreSQL TLS / version if applicable
    with engine.connect() as conn:
        try:
            db_version = conn.execute(text("SELECT version();")).scalar()
            print(f"Server Version: {db_version.split(',')[0] if db_version else 'Unknown'}")
        except Exception:
            pass

    # 3. Create tables idempotently
    print("\n[2/3] Creating/verifying database schema tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables verified:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

    # 4. Inspect table status (seeding disabled per production audit policy)
    print("\n[3/3] Inspecting table status (seeding disabled pending external verification)...")
    session = SessionLocal()
    try:
        benchmark_count = session.query(func.count(CompanyBenchmark.id)).scalar() or 0
        total_analyses = session.query(func.count(JobAnalysis.id)).scalar() or 0
        print(f"Company benchmarks present: {benchmark_count}")
        print(f"Current stored analyses in audit trail: {total_analyses}")
        print("Note: Automated benchmark seeding is deferred until manual data verification.")
    except Exception as exc:
        print(f"WARNING: Inspection error (non-fatal): {exc}")
    finally:
        session.close()

    print("\n" + "=" * 70)
    print("Database initialization completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    initialize_database()
