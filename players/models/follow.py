from django.db import models
from common.models import CommonFields


class Follow(CommonFields):
    follower = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="followers")

    class Meta:
        unique_together = ("follower", "following", )
