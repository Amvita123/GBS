from django.db import models
from common.models import CommonFields


class ChatNotification(CommonFields):
    last_message = models.CharField(max_length=255, null=True, blank=True)
    count = models.IntegerField(default=1)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    group = models.ForeignKey("chatapp.ChallengeGroupChat", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "group")

