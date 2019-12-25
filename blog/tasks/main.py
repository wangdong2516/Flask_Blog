from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379/8', backend='redis://localhost:6379/8')