"""
Celery application for InfoTrust.
Provides scheduled (Beat) and on-demand task execution.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fake_news_detector.settings')

app = Celery('fake_news_detector')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'auto-scrape-every-hour': {
        'task': 'news.tasks.auto_scrape_news',
        'schedule': crontab(minute=0),      # runs at :00 of every hour
        'options': {'expires': 55 * 60},    # discard if not picked up within 55 min
    },
}

app.conf.timezone = 'UTC'
