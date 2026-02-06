from common.models import CommonFields
from django.db import models
from django.utils.timezone import now


class Challenge(CommonFields):
    status_choices = (
        ("completed", "completed"),
        ("pending", "pending")
    )
    challenge_id = models.CharField(max_length=12, unique=True, editable=False)
    first_squad = models.ForeignKey("players.Squad", on_delete=models.CASCADE, related_name="first_squad")
    # first squad is challenger
    second_squad = models.ForeignKey("players.Squad", on_delete=models.CASCADE, related_name="second_squad")
    result_date = models.DateField()
    status = models.CharField(max_length=20, choices=status_choices, default="pending")
    is_accepted = models.BooleanField(null=True, blank=True)
    winner = models.ForeignKey("players.Squad", on_delete=models.CASCADE, related_name="winner", null=True, blank=True)
    point_first_squad = models.IntegerField(null=True, blank=True)
    point_second_squad = models.IntegerField(null=True, blank=True)

    def save(
            self,
            *args,
            **kwargs
    ):
        if self._state.adding:
            self.challenge_id = now().strftime("%y%m%d%H%M%S")
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("first_squad", "second_squad", "result_date")

    def __str__(self):
        return self.challenge_id

