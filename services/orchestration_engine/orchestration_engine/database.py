# services/orchestration_engine/orchestration_engine/database.py

import sqlite3
import logging

DB_FILE = "workflows.db"
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the workflows table if it doesn't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tasks TEXT NOT NULL,
                status TEXT NOT NULL,
                results TEXT
            );
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")

if __name__ == '__main__':
    # This allows us to initialize the database from the command line
    logging.basicConfig(level=logging.INFO)
    init_db()
