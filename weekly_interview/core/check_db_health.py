"""
Database Health Check Script

To run this script, navigate to the project root ('App' directory) and execute:
python -m weekly_interview.core.check_db_health

This runs the script as a module, which correctly handles the relative imports.
"""

import asyncio
import json
import logging
import sys

# Relative imports work because this script lives inside the 'core' package
from .database import DatabaseManager
from .ai_services import SharedClientManager

# Configure logging for clear output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _sync_test_mysql(db_manager: DatabaseManager):
    """Synchronous helper to run the MySQL version check in an executor."""
    conn = db_manager.get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        (version,) = cursor.fetchone()
        return version
    finally:
        conn.close()

async def test_mysql_fetch(db_manager: DatabaseManager, executor):
    """Performs a simple SELECT query on MySQL to verify connection and permissions."""
    logging.info("--- [1/2] Testing MySQL Fetch ---")
    try:
        loop = asyncio.get_event_loop()
        version = await loop.run_in_executor(executor, _sync_test_mysql, db_manager)
        logging.info(f"? MySQL connection successful. Server version: {version}")
        return True
    except Exception as e:
        logging.error(f"? MySQL fetch failed: {e}", exc_info=False)
        return False

async def test_mongodb_fetch(db_manager: DatabaseManager):
    """Connects to MongoDB, gets server info, and lists collections."""
    logging.info("--- [2/2] Testing MongoDB Fetch ---")
    try:
        client = await db_manager.get_mongo_client()
        if not client:
            logging.error("? MongoDB client could not be initialized.")
            return False
            
        server_info = await client.server_info()
        logging.info(f"? MongoDB connection successful. Server version: {server_info.get('version', 'N/A')}")

        # Also try to list collections in the default database
        db = await db_manager.get_mongo_db()
        logging.info(f"   Checking collections in database: '{db.name}'")
        collections = await db.list_collection_names()
        
        if collections:
            logging.info(f"   Found {len(collections)} collections. Sample: {collections[:5]}")
        else:
            logging.info("   No collections found in the default database.")
        return True
    except Exception as e:
        logging.error(f"? MongoDB fetch failed: {e}", exc_info=False)
        return False

async def main():
    """
    Performs a detailed health check on the databases (MySQL and MongoDB)
    by attempting to fetch data from each.
    """
    logging.info("?? Starting database health check...")

    shared_client_manager = None
    db_manager = None

    try:
        shared_client_manager = SharedClientManager()
        db_manager = DatabaseManager(client_manager=shared_client_manager)

        mysql_ok = await test_mysql_fetch(db_manager, shared_client_manager.executor)
        mongo_ok = await test_mongodb_fetch(db_manager)

        print("-" * 40)
        if mysql_ok and mongo_ok:
            logging.info("?? Overall database status: HEALTHY")
        else:
            logging.error("?? Overall database status: UNHEALTHY. Check logs above for details.")

    except Exception as e:
        logging.error(f"? An unexpected error occurred during setup: {e}", exc_info=True)
    finally:
        if db_manager:
            await db_manager.close_connections()
            logging.info("Database connections closed.")
        if shared_client_manager:
            await shared_client_manager.close_connections()
        logging.info("?? Health check script finished.")

if __name__ == "__main__":
    # This check prevents running the script directly, which causes an ImportError.
    # It must be run as a module from the project root.
    if __package__ is None or __package__ == '':
        print("ERROR: This script cannot be run directly.", file=sys.stderr)
        print("Please execute it from the project root ('App' directory) using:", file=sys.stderr)
        print(f"    python -m weekly_interview.core.check_db_health", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main())