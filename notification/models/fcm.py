from django.db import models
from users.models import User
from common.models import CommonFields


class FCMToken(CommonFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fcm_tokens")
    token = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=150, blank=True, null=True)
    browser = models.CharField(max_length=50, blank=True, null=True)



