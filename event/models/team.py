from django.db import models
from common.models import CommonFields


class Team(models.Model):
    name = models.CharField(max_length=255,)
    grade = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)


class EventTeamUser(CommonFields):
    event = models.ForeignKey(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="event_team",
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        limit_choices_to=models.Q(user_role='player') | models.Q(user_role='coach')
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE
    )

    created_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="team_create_by"
    )

    class Meta:
        unique_together = ("event", "user")
