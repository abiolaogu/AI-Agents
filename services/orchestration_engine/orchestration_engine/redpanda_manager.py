import logging
import json
import asyncio
from aiokafka import AIOKafkaProducer
import os

class RedpandaManager:
    """Manages event streaming to Redpanda."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.bootstrap_servers = os.getenv("REDPANDA_BROKERS", "redpanda:29092")
        self.producer = None

    async def start(self):
        """Starts the Redpanda producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers
            )
            await self.producer.start()
            self.logger.info(f"Connected to Redpanda at {self.bootstrap_servers}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redpanda: {e}")

    async def stop(self):
        """Stops the Redpanda producer."""
        if self.producer:
            await self.producer.stop()

    async def publish_event(self, topic: str, event: dict):
        """Publishes an event to a Redpanda topic."""
        if not self.producer:
            self.logger.warning("Redpanda producer not initialized. Skipping event.")
            return

        try:
            value_json = json.dumps(event).encode('utf-8')
            await self.producer.send_and_wait(topic, value_json)
            self.logger.debug(f"Published event to {topic}: {event}")
        except Exception as e:
            self.logger.error(f"Failed to publish event to {topic}: {e}")
