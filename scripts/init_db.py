"""
scripts/init_db.py
-------------------
Initialize the MySQL database: create tables and seed default settings.

Usage:
    python scripts/init_db.py
    python scripts/init_db.py --drop-all  # WARNING: destroys all data
"""

import sys
import pathlib
import argparse
import logging

# Add project root to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Initialize EnergyPulse database")
    parser.add_argument("--drop-all", action="store_true", help="Drop and recreate all tables")
    args = parser.parse_args()

    from backend.app.services.db import init_db, get_engine

    log.info("Connecting to database...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            log.info("Database connection OK.")
    except Exception as exc:
        log.error("Cannot connect to database: %s", exc)
        log.error(
            "\nTroubleshooting:\n"
            "  1. Ensure MySQL is running\n"
            "  2. Copy .env.example to .env and set correct credentials\n"
            "  3. Create the database: CREATE DATABASE energypulse;\n"
            "  4. Create user: CREATE USER 'energyuser'@'localhost' IDENTIFIED BY 'energypass123';\n"
            "  5. Grant privileges: GRANT ALL ON energypulse.* TO 'energyuser'@'localhost';\n"
            "  6. Or use Docker: docker-compose up -d mysql"
        )
        sys.exit(1)

    if args.drop_all:
        confirm = input("WARNING: This will drop ALL tables. Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            log.info("Aborted.")
            sys.exit(0)

    init_db(drop_all=args.drop_all)
    log.info("Database initialized successfully.")


if __name__ == "__main__":
    main()
