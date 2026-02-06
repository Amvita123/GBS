from celery import shared_task
from chatapp.models import ChallengeGroupChat, PersonalChat
from datetime import datetime, timedelta


@shared_task
def delete_challenge_chat_before_24():
    chats = ChallengeGroupChat.objects.all()
    now = datetime.now()
    for chat in chats:
        hours_diff = (now - chat.created_at).total_seconds() / 3600
        if hours_diff > 24:
            chat.delete()

    return "challenge chat deleted successfully."


@shared_task
def delete_personal_chat_before_24_hours():
    chats = PersonalChat.objects.all()
    now = datetime.now()
    for chat in chats:
        hours_diff = (now - chat.created_at).total_seconds() / 3600
        if hours_diff > 24:
            chat.delete()

