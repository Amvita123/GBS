from firebase_admin import messaging
from celery import shared_task
from notification.models import FCMToken, Notification
from users.models import User

@shared_task
def send_notification(username, title, message):
    fcm_token_list = list(FCMToken.objects.select_related("user").filter(user__username=username).values_list("token", flat=True))
    responses = []
    try:
        formatted_message = " ".join(message.split())
        for fcm_token in fcm_token_list:
            notification_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=formatted_message
                ),
                token=fcm_token,
            )
            response = messaging.send(notification_message)
            responses.append(response)
        return {"status": "success", "response": responses}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@shared_task
def send_user_action_notification(action, sender, receiver, object_id="",  message="", title=""):
    # if action == "share_post":
    #     message = f"{sender} has share post"

    sender = User.objects.get(username=sender)
    receiver = User.objects.get(username=receiver)
    notification = Notification.objects.create(
        title=title,
        from_user=sender,
        to_user=receiver,
        action=action,
        message=message
    )

    if object_id:
        notification.is_action = True
        notification.objects_id = object_id
        notification.save()

    try:
        send_notification.delay(username=receiver.username, title=title, message=message)
    except:
        pass

    return f"notification has been sent to {receiver.username}"


