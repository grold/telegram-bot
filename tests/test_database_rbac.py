import sqlite3
import pytest
import os
from unittest.mock import patch
from database import init_db, DATABASE_PATH

@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Sets up a temporary database for testing."""
    db_path = tmp_path / "test_rbac.db"
    with patch("database.DATABASE_PATH", str(db_path)):
        init_db()
        yield db_path

def test_user_schema_has_rbac_columns():
    """Verifies that the users table has the required RBAC columns."""
    # init_db is called by fixture
    from database import DATABASE_PATH
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    assert "role" in columns
    assert "is_authorized" in columns
    assert columns["is_authorized"].upper() in ["BOOLEAN", "INTEGER"] # SQLite types can vary

def test_command_permissions_table_exists():
    """Verifies that the command_permissions table is created."""
    # init_db is called by fixture
    from database import DATABASE_PATH
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='command_permissions'")
    assert cursor.fetchone() is not None
