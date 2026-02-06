from django.db import models
from users.models import User
from common.models import CommonFields


class Notification(CommonFields):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender", null=True, blank=True)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")
    title = models.CharField(max_length=255, null=True)
    message = models.TextField()
    challenge = models.ForeignKey(
        "players.Challenge", on_delete=models.CASCADE, related_name="challenge",
        blank=True, null=True
    )
    action = models.CharField(max_length=50, null=True, blank=True, default="")
    objects_id = models.UUIDField(null=True, blank=True)
    is_action = models.BooleanField(default=False)


class PushNotification(CommonFields):
    Notification_TO = (
        ("player", "Player"),
        ("fan", "Fan"),
        ("coach", "Coach"),
        ("event", "Event"),
        ("sub-admin", "Sub-Admin"),
    )

    title = models.CharField(max_length=255, null=True)
    message = models.TextField()
    to = models.CharField(max_length=50, choices=Notification_TO)
    schedule = models.DateTimeField(null=True, blank=True)
    event = models.ForeignKey("event.Event", on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True)
    sent = models.BooleanField(default=False)
