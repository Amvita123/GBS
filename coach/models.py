from django.db import models
from common.models import CommonFields


class CoachType(CommonFields):
    name = models.CharField(max_length=100, unique=True)


class OrganizationPlayer(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)


class Organization(CommonFields):
    logo = models.ImageField(upload_to="organization/")
    name = models.CharField(max_length=255)
    biograph = models.TextField(null=True, blank=True)
    sport = models.ForeignKey("players.Sport", on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="organization", null=True,
                                   blank=True)


class OrganizationTransaction(CommonFields):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="transaction")
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="organization_transaction",
        limit_choices_to={"user_role": "coach"},
        null=True, blank=True
    )

    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    payer_info = models.JSONField(null=True, blank=True)

    amount = models.IntegerField()
    currency = models.CharField(max_length=10, default="usd")

    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("succeeded", "Succeeded"),
            ("failed", "Failed"),
            ("canceled", "Canceled"),
        ],
        default="pending"
    )


class Roster(CommonFields):
    name = models.CharField(max_length=255)
    # players = models.ManyToManyField("users.User", related_name="roster_player")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="roster")
    # coaches = models.ManyToManyField("users.User", related_name="roster")
    grade = models.ForeignKey("coach.RosterGrade", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class RosterPlayer(CommonFields):
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name="roster_player")
    player = models.ForeignKey("users.User", on_delete=models.CASCADE, limit_choices_to={"user_role": "player"})
    jersey_number = models.CharField(max_length=10, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = [
            ['roster', 'player'],
            ['roster', 'jersey_number']  # Ensures unique jersey per roster
        ]
        db_table = 'coach_roster_player'


class RosterCoach(CommonFields):
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name="roster_coach")
    coach = models.ForeignKey("users.User", on_delete=models.CASCADE, limit_choices_to={"user_role": "coach"})
    jersey_number = models.CharField(max_length=10, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = [
            ['roster', 'coach'],
            ['roster', 'jersey_number']  # Ensures unique jersey per roster
        ]
        db_table = 'coach_roster_coach'


class InvitePlayer(CommonFields):
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name="invite", blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("accept", "Accept"),
            ("reject", "Reject")
        ],
        default="pending"
    )
    phone_number = models.CharField(max_length=15, null=True, blank=True)


class RosterGrade(CommonFields):
    name = models.CharField(max_length=50, unique=True)


class RosterExitRequest(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE,
                             limit_choices_to={"user_role__in": ["coach", "player"]}
                             )

    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name="roster_exit_request")
    is_exit = models.BooleanField(default=False)


