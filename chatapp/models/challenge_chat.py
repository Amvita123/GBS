from common.models import CommonFields
from django.db import models


class ChallengeGroupChat(CommonFields):
    users = models.ForeignKey(
        "users.User", on_delete=models.SET_DEFAULT, default="Anonymous",
        related_name="message_sender", limit_choices_to={"user_role": "player"},
    )
    challenge = models.ForeignKey(
        "players.Challenge", on_delete=models.CASCADE,
        related_name="challenges"
    )
    message = models.TextField()
    is_edit = models.BooleanField(default=False)


