from celery import shared_task
from .sender import send_notification
from notification.models import Notification
from users.models import User
from players.models import Challenge
from datetime import datetime


@shared_task
def send_challenge_request_notification(sender, receiver, challenge, message, is_action=False, action=False):
    sender = User.objects.get(username=sender)
    receiver = User.objects.get(username=receiver)

    destination = ""
    if action:
        challenge_obj = Challenge.objects.filter(id=challenge).first()
        if challenge_obj:
            if challenge_obj.result_date > datetime.now().date():
                destination = "upcoming_challenge"
            elif challenge_obj.result_date < datetime.now().date():
                destination = "past_challenge"
            else:
                destination = "today_challenge"

    Notification.objects.create(
        from_user=sender,
        to_user=receiver,
        message=message,
        challenge_id=challenge,
        is_action=is_action,
        action=destination if action is True else ''
    )

    send_notification.delay(
        username=receiver.username,
        title="Athlete Rated Challenge.",
        message=message
    )

    return f"notification sent: {message}"


@shared_task
def disable_notification_action(challenge_id):
    Notification.objects.filter(challenge_id=challenge_id).update(
        is_action=False, is_active=False
    )
    return f"notifications action disabled for {challenge_id}"



