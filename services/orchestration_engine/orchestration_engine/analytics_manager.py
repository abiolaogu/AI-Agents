import logging
from datetime import datetime, timezone
from sqlalchemy import select
from .database import get_db_session, AnalyticsEvent

class AnalyticsManager:
    """Manages the logging of analytics events to the database."""

    def __init__(self, logger: logging.Logger, redpanda_manager=None):
        self.logger = logger
        self.redpanda_manager = redpanda_manager

    async def log_event(self, event_type: str, workflow_id: str = None, agent_id: str = None,
                  duration: float = None, status: str = None, user_id: int = None):
        """
        Logs an analytics event to the database and streams it to Redpanda.
        """
        try:
            # Stream to Redpanda
            if self.redpanda_manager:
                event_data = {
                    "event_type": event_type,
                    "workflow_id": workflow_id,
                    "agent_id": agent_id,
                    "duration": duration,
                    "status": status,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await self.redpanda_manager.publish_event("analytics_events", event_data)

            # Log to Database
            session = await get_db_session()
            try:
                event = AnalyticsEvent(
                    event_type=event_type,
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    duration=duration,
                    status=status,
                    user_id=user_id
                )
                session.add(event)
                await session.commit()
            finally:
                await session.close()
        except Exception as e:
            self.logger.error(f"Failed to log analytics event: {e}")

    async def get_events_for_user(self, user_id: int) -> list:
        """Retrieves all analytics events for a given user."""
        try:
            session = await get_db_session()
            try:
                result = await session.execute(
                    select(AnalyticsEvent)
                    .where(AnalyticsEvent.user_id == user_id)
                    .order_by(AnalyticsEvent.timestamp.desc())
                )
                events = result.scalars().all()
                return [
                    {
                        "id": e.id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "workflow_id": e.workflow_id,
                        "agent_id": e.agent_id,
                        "duration": e.duration,
                        "status": e.status,
                        "user_id": e.user_id
                    }
                    for e in events
                ]
            finally:
                await session.close()
        except Exception as e:
            self.logger.error(f"Failed to fetch analytics events for user {user_id}: {e}")
            return []
