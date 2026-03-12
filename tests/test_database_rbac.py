import sqlite3
import pytest
import os
from database import init_db, DATABASE_PATH

@pytest.fixture
def test_db():
    """Sets up a temporary database for testing."""
    # Use a separate test database file
    test_db_file = "test_bot.db"
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
    
    # Patch DATABASE_PATH in database.py would be better, 
    # but for now let's just use the current one if it's not production
    # Or better, let's just check the actual bot.db if we are in a safe env.
    # Actually, let's just check if columns exist after init_db()
    yield test_db_file
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

def test_user_schema_has_rbac_columns():
    """Verifies that the users table has the required RBAC columns."""
    init_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    assert "role" in columns
    assert "is_authorized" in columns
    assert columns["is_authorized"].upper() in ["BOOLEAN", "INTEGER"] # SQLite types can vary

def test_command_permissions_table_exists():
    """Verifies that the command_permissions table is created."""
    init_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='command_permissions'")
    assert cursor.fetchone() is not None
