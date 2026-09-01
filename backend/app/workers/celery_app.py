"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "zenglow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute
    beat_schedule={
        # Send 24-hour reminders every 30 minutes
        "appointment-reminders-24h": {
            "task": "app.workers.tasks.send_appointment_reminders",
            "schedule": crontab(minute="*/30"),
            "args": (24,),
        },
        # Send 2-hour reminders every 15 minutes
        "appointment-reminders-2h": {
            "task": "app.workers.tasks.send_appointment_reminders",
            "schedule": crontab(minute="*/15"),
            "args": (2,),
        },
        # Payment reconciliation daily at 2am
        "payment-reconciliation": {
            "task": "app.workers.tasks.reconcile_payments",
            "schedule": crontab(hour=2, minute=0),
        },
        # Review requests — daily at 6pm
        "review-requests": {
            "task": "app.workers.tasks.send_review_requests",
            "schedule": crontab(hour=18, minute=0),
        },
    },
)
