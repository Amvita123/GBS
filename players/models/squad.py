from common.models import CommonFields
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.timezone import now
from django.core.validators import FileExtensionValidator
from django.contrib.postgres.fields import ArrayField


class Squad(CommonFields):
    name = models.CharField(max_length=155)
    created_by = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="owner")
    players = models.ManyToManyField(
        "users.User", limit_choices_to={"user_role": "player"},
    )
    win = models.PositiveIntegerField(default=0)
    loss = models.PositiveIntegerField(default=0)
    squad_id = models.CharField(max_length=12, unique=True, editable=False, auto_created=True, null=True)
    logo = models.ImageField(upload_to="squad/", null=True, blank=True,
                             validators=[
                                 FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic'])]
                             )

    structure = models.ForeignKey("players.SquadStructure", on_delete=models.PROTECT, null=True, blank=True)

    # def clean(self):
    #     super().clean()
    #     if self.players.count() > 5:
    #         raise ValidationError("You can only have a maximum of 5 players.")
    #
    def save(self, *args, **kwargs):
        # self.full_clean()
        if self._state.adding:
            self.squad_id = now().strftime("%y%m%d%H%M%S")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.created_by.username}"


class SquadStructure(models.Model):
    structure_position = [
        ("PG", "Point Guard"),
        ("SG", "Shooting Guard"),
        ("CG", "Combo Guard"),
        ("SF", "Small Forward"),
        ("WING", "Wing"),
        ("STRETCH BIG", "Stretch Big"),
        ("PF", "Power Forward"),
        ("C", "Center")
    ]
    structure = models.CharField(max_length=100)
    rating = models.IntegerField()
    position_1 = ArrayField(models.CharField(max_length=15, choices=structure_position), default=list)
    position_2 = ArrayField(models.CharField(max_length=15, choices=structure_position), default=list)
    position_3 = ArrayField(models.CharField(max_length=15, choices=structure_position), default=list)
    position_4 = ArrayField(models.CharField(max_length=15, choices=structure_position), default=list)
    position_5 = ArrayField(models.CharField(max_length=15, choices=structure_position), default=list)

    def __str__(self):
        return self.structure


