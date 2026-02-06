from celery import shared_task
from notification.models import Notification, PushNotification
from users.models import User
from .sender import send_notification
from event.models import Event, EventCheckIn
from django.utils import timezone
import traceback


@shared_task
def push_admin_notification(user_type, title, message):
    users = User.objects.filter(user_role=user_type, is_active=True)
    admin = User.objects.filter(is_superuser=True).first()
    notifications = []
    for user in users:
       notifications.append(
           Notification(
               from_user=admin,
               to_user=user,
               title=title,
               message=message,
               action="admin"
           )
       )
       send_notification.delay(
           username=user.username,
           title=title,
           message=message
       )
    Notification.objects.bulk_create(notifications)
    return f"admin notification pushed to {user_type}"


@shared_task
def send_single_user_admin_notification(
        username,
        user_id,  # receiver id
        title,
        message,
        action="",
        object_id="",
        from_user_id="",
        is_action=False

):

    send_notification.delay(
        username=username,
        title=title,
        message=message
    )
    option_fields = {}
    if from_user_id:
        option_fields['from_user_id'] = from_user_id

    if object_id:
        option_fields["objects_id"] = object_id

    try:
        Notification.objects.create(
            to_user_id=user_id,
            title=title,
            message=message,
            action=action,
            is_action=is_action,
            **option_fields
        )

    except Exception as e:
        print(e)
        traceback.print_exc()

    return f"notification sent successfully to {username}"


@shared_task
def send_event_notification(event_id, title, message):
    followers_users = User.objects.filter(eventfollower__event_id=event_id)
    user_ids = EventCheckIn.objects.filter(event_id=event_id).values_list('user_id', flat=True)
    checkin_users = User.objects.filter(id__in=user_ids)

    merged_users = (followers_users | checkin_users).distinct()
    for user in merged_users:
        send_notification.delay(
            username=user.username,
            title=title,
            message=message
        )

    return f"event {event_id} notification sent successfully"


@shared_task(name='notification.task.send_scheduler_notifications')
def send_scheduler_notifications():
    now = timezone.now()
    notifications = PushNotification.objects.filter(
        schedule__lte=now,
        sent=False
    )

    for notification in notifications:
        if notification.to == "event":
            send_event_notification.delay(
                event_id=notification.event.id,
                title=notification.title,
                message=notification.message
            )
        else:
            push_admin_notification.delay(
                user_type=notification.to,
                title=notification.title,
                message=notification.message
            )
        notification.sent = True
        notification.save()

    return "schedule notification task run."


