import sqlite3
import logging
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

def init_db():
    """Initializes the SQLite database with the users table."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_sharing BOOLEAN DEFAULT 0,
            latitude REAL,
            longitude REAL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def update_user_status(user_id, username, full_name, is_sharing):
    """Updates a user's sharing status and basic info."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, full_name, is_sharing)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name,
            is_sharing=excluded.is_sharing
    ''', (user_id, username, full_name, is_sharing))
    conn.commit()
    conn.close()

def update_user_location(user_id, latitude, longitude):
    """Updates a user's coordinates and timestamp."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (latitude, longitude, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    """Retrieves a user's record from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_sharing_users():
    """Returns a list of all users who are currently sharing their location."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_sharing = 1')
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_by_username(username):
    """Retrieves a user by their username (case-insensitive)."""
    if username.startswith('@'):
        username = username[1:]
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
    user = cursor.fetchone()
    conn.close()
    return user
