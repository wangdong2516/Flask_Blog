"""
    celery任务
"""

from celery import Celery


celery_app = Celery('blog', broker='redis://localhost:6379/8')


celery_app.autodiscover_tasks(['celery_tasks.email'])