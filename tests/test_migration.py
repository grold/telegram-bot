import os
import sqlite3
import pytest
from database import init_db, DATABASE_PATH, get_user
from tools.migrate_auth import migrate_auth_file, AUTH_FILE, AUTH_BAK_FILE

@pytest.fixture
def clean_db():
    """Ensures a clean database and auth file for testing."""
    init_db()
    # Clear existing users for clean test
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    
    if os.path.exists(AUTH_FILE):
        os.remove(AUTH_FILE)
    if os.path.exists(AUTH_BAK_FILE):
        os.remove(AUTH_BAK_FILE)
    
    yield
    
    if os.path.exists(AUTH_FILE):
        os.remove(AUTH_FILE)
    if os.path.exists(AUTH_BAK_FILE):
        os.remove(AUTH_BAK_FILE)

def test_migration_from_auth_file(clean_db):
    """Verifies that user IDs from .auth are migrated to DB."""
    # Create a mock .auth file
    with open(AUTH_FILE, "w") as f:
        f.write("12345\n67890\n")
    
    migrate_auth_file()
    
    # Verify DB state
    user1 = get_user(12345)
    assert user1 is not None
    assert user1["role"] == "OWNER"
    assert user1["is_authorized"] == 1
    
    user2 = get_user(67890)
    assert user2 is not None
    assert user2["role"] == "ADMIN"
    assert user2["is_authorized"] == 1
    
    # Verify file was renamed
    assert not os.path.exists(AUTH_FILE)
    assert os.path.exists(AUTH_BAK_FILE)
