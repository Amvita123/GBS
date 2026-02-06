from django.db import models
from common.models import CommonFields


class EventCheckIn(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="event_check_in")
    event = models.ForeignKey("event.Event", on_delete=models.CASCADE)
    # squad = models.ForeignKey("Squad", on_delete=models.CASCADE)
    squad = models.CharField(max_length=255, blank=True, null=True)
    jersey_number = models.IntegerField(null=True, blank=True)
    roster = models.ForeignKey("coach.Roster", on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey("event.Team", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ("event", "user")

