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
            role TEXT DEFAULT 'USER',
            is_authorized BOOLEAN DEFAULT 0,
            is_sharing BOOLEAN DEFAULT 0,
            latitude REAL,
            longitude REAL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_permissions (
            command TEXT PRIMARY KEY,
            min_role TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            chat_id INTEGER,
            chat_type TEXT,
            chat_title TEXT,
            message_id INTEGER,
            content TEXT,
            duration_ms REAL,
            bot_version TEXT
        )
    ''')
    
    # Simple migration: Add role and is_authorized if they don't exist
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "USER"')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_authorized BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass

    # Simple migration: Add chat_username if it doesn't exist
    try:
        cursor.execute('ALTER TABLE logs ADD COLUMN chat_username TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()

def add_interaction_log(user_id, username, full_name, chat_id, chat_type, chat_title, message_id, content, duration_ms, bot_version, chat_username=None):
    """Adds a new interaction log entry to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (
            user_id, username, full_name, chat_id, chat_type, chat_title, 
            message_id, content, duration_ms, bot_version, chat_username
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, chat_id, chat_type, chat_title, message_id, content, duration_ms, bot_version, chat_username))
    conn.commit()
    conn.close()

def get_recent_logs(limit=10, query=None):
    """Retrieves the most recent interaction logs with optional filtering."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = 'SELECT * FROM logs'
    params = []
    
    if query:
        # Search in username, full_name, chat_title, or content
        sql += ''' WHERE 
            username LIKE ? OR 
            full_name LIKE ? OR 
            chat_title LIKE ? OR 
            content LIKE ? '''
        search_term = f'%{query}%'
        params.extend([search_term, search_term, search_term, search_term])
        
    sql += ' ORDER BY timestamp DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(sql, params)
    logs = cursor.fetchall()
    conn.close()
    return logs

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

def get_command_min_role(command):
    """Retrieves the minimum role required for a command."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT min_role FROM command_permissions WHERE command = ?', (command,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_command_min_role(command, min_role):
    """Sets the minimum role required for a command."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO command_permissions (command, min_role)
        VALUES (?, ?)
        ON CONFLICT(command) DO UPDATE SET min_role=excluded.min_role
    ''', (command, min_role))
    conn.commit()
    conn.close()

def grant_user_access(user_id, role, username=None, full_name=None):
    """Grants or updates user access and role."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, full_name, role, is_authorized)
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            username=COALESCE(excluded.username, users.username),
            full_name=COALESCE(excluded.full_name, users.full_name),
            role=excluded.role,
            is_authorized=1
    ''', (user_id, username, full_name, role))
    conn.commit()
    conn.close()

def revoke_user_access(user_id):
    """Revokes user access (sets is_authorized to 0)."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_authorized = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_authorized_users_db():
    """Returns a list of all authorized users."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE is_authorized = 1')
    users = cursor.fetchall()
    conn.close()
    return users

def ensure_user(user_id, username=None, full_name=None):
    """Ensures a user exists in the database with basic info."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=COALESCE(excluded.username, users.username),
            full_name=COALESCE(excluded.full_name, users.full_name)
    ''', (user_id, username, full_name))
    conn.commit()
    conn.close()

def get_known_groups():
    """Retrieves a list of groups the bot has interacted with, ordered by most recent interaction."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id, chat_title, chat_username, MIN(timestamp) as first_seen, MAX(timestamp) as last_seen 
        FROM logs 
        WHERE chat_type IN ('group', 'supergroup') 
        GROUP BY chat_id 
        ORDER BY last_seen DESC
    ''')
    groups = cursor.fetchall()
    conn.close()
    return groups
