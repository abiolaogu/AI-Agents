# services/orchestration_engine/orchestration_engine/analytics_manager.py

import logging
from .database import get_db_connection

class AnalyticsManager:
    """Manages the logging of analytics events to the database."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_event(self, event_type: str, workflow_id: str = None, agent_id: str = None,
                  duration: float = None, status: str = None, user_id: int = None):
        """
        Logs an analytics event to the database.
        """
        try:
            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO analytics_events (event_type, workflow_id, agent_id, duration, status, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_type, workflow_id, agent_id, duration, status, user_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log analytics event: {e}")

    def get_events_for_user(self, user_id: int) -> list:
        """Retrieves all analytics events for a given user."""
        try:
            conn = get_db_connection()
            events_cursor = conn.execute("SELECT * FROM analytics_events WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()
            conn.close()
            return [dict(row) for row in events_cursor]
        except Exception as e:
            self.logger.error(f"Failed to fetch analytics events for user {user_id}: {e}")
            return []
