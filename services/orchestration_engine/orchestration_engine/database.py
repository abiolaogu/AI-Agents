# services/orchestration_engine/orchestration_engine/database.py

import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = "workflows.db"
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        """)

        # Create workflows table with a foreign key to users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tasks TEXT NOT NULL,
                status TEXT NOT NULL,
                results TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        # Create analytics events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                workflow_id TEXT,
                agent_id TEXT,
                duration REAL,
                status TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")

def hash_password(password: str) -> str:
    """Hashes a password for storing."""
    return generate_password_hash(password)

def check_password(password_hash: str, password: str) -> bool:
    """Checks a password against a hash."""
    return check_password_hash(password_hash, password)

if __name__ == '__main__':
    # This allows us to initialize the database from the command line
    logging.basicConfig(level=logging.INFO)
    init_db()
