import os

from celery import Celery

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Create Celery app
app = Celery("medical_translation")

# Load config from Django settings with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Explicitly import tasks module to register Celery signals
# This ensures message bus is registered in worker processes
app.conf.imports = ("api.tasks",)

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Disable celery logs hijacking as we manage our own logging
app.conf.update(
    worker_hijack_root_logger=False,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
