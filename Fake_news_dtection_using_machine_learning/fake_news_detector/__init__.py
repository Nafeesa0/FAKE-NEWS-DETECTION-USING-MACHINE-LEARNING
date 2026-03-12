# Make Celery app available as part of the Django project
from .celery import app as celery_app

__all__ = ('celery_app',)
