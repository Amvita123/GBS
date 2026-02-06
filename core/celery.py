import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

if os.name == "nt":
    from multiprocessing import set_start_method
    set_start_method("spawn", force=True)

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-notifications-every-minute': {
        'task': 'notification.task.send_scheduler_notifications',
        'schedule': crontab(),
    },

    'delete_personal_chat_before_24_hours': {
        'task': 'chatapp.tasks.delete_personal_chat_before_24_hours',
        'schedule': crontab(minute='*/10'),
        'args': ()
    },

    'delete_group_chat_before_24_hours': {
        'task': 'chatapp.tasks.delete_challenge_chat_before_24',
        'schedule': crontab(hour=0, minute=1),
        'args': ()
    },

    'check-verification-expiry-daily': {
        'task': 'users.task.handle_verification_expiry',
        # 'schedule': crontab(minute='*/1'),
        'schedule': crontab(hour=0, minute=1),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

