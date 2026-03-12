import os
import sqlite3
import logging
from database import DATABASE_PATH

logger = logging.getLogger(__name__)

AUTH_FILE = ".auth"
AUTH_BAK_FILE = ".auth.bak"

def migrate_auth_file():
    """Migrates authorized user IDs from .auth file to SQLite database."""
    if not os.path.exists(AUTH_FILE):
        logger.info(f"No {AUTH_FILE} found. Skipping migration.")
        return

    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            user_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
        
        if not user_ids:
            logger.info(f"{AUTH_FILE} is empty. Renaming to {AUTH_BAK_FILE}.")
            os.rename(AUTH_FILE, AUTH_BAK_FILE)
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # First ID is OWNER, others are ADMIN
        for i, user_id in enumerate(user_ids):
            role = "OWNER" if i == 0 else "ADMIN"
            logger.info(f"Migrating user {user_id} with role {role}")
            
            cursor.execute('''
                INSERT INTO users (user_id, role, is_authorized)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    role=excluded.role,
                    is_authorized=1
            ''', (user_id, role))
        
        conn.commit()
        conn.close()
        
        # Rename the file after successful migration
        os.rename(AUTH_FILE, AUTH_BAK_FILE)
        logger.info(f"Successfully migrated {len(user_ids)} users. {AUTH_FILE} renamed to {AUTH_BAK_FILE}.")
        
    except Exception as e:
        logger.error(f"Error during migration from {AUTH_FILE}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_auth_file()
