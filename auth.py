import sqlite3
import bcrypt
import streamlit as st
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the SQLite database with users table."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            openai_api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, password_hash):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def register_user(username, email, password):
    """Register a new user."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Check if username or email already exists
        c.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            conn.close()
            return False, "Username or email already exists"
        
        # Hash password and store user
        password_hash = hash_password(password)
        c.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        return True, "Registration successful"
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False, "Registration failed"

def login_user(username, password):
    """Authenticate a user."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Get user by username
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        
        if user and verify_password(password, user[3]):  # user[3] is password_hash
            # Update last login
            c.execute('UPDATE users SET last_login = ? WHERE username = ?',
                     (datetime.now(), username))
            conn.commit()
            conn.close()
            return True, {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "created_at": user[4],
                "last_login": user[5]
            }
        conn.close()
        return False, "Invalid username or password"
    except Exception as e:
        logger.error(f"Login error: {e}")
        return False, "Login failed"

def get_user_by_id(user_id):
    """Get user details by ID."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "created_at": user[4],
                "last_login": user[5]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def update_openai_api_key(username, api_key):
    """Update user's OpenAI API key."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET openai_api_key = ? WHERE username = ?',
                 (api_key, username))
        conn.commit()
        conn.close()
        return True, "API key updated successfully"
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        return False, "Failed to update API key"

def get_openai_api_key(username):
    """Get user's OpenAI API key."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT openai_api_key FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting API key: {e}")
        return None

# Initialize database when module is imported
init_db() 