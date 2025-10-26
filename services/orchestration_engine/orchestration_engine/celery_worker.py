# services/orchestration_engine/orchestration_engine/celery_worker.py

from celery import Celery
import logging

# In a real app, this would come from config
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

celery = Celery(
    'orchestration_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['services.orchestration_engine.orchestration_engine.tasks']
)

celery.conf.update(
    task_track_started=True,
)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    celery.start()
