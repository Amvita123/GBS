from django.db import models
from common.models import CommonFields


class EventFollower(CommonFields):
    event = models.ForeignKey("event.Event", on_delete=models.CASCADE, related_name="event_follower")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("event", "user")
