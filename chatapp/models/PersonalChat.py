from django.db import models
from common.models import CommonFields


class PersonalChat(CommonFields):
    sender = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="sender_user")
    receiver = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="receiver_user")
    message = models.TextField(null=True, blank=True)
    post = models.ForeignKey("common.Feed", on_delete=models.SET_NULL, null=True, blank=True)
