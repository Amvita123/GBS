from common.models import CommonFields
from django.db import models
from .player import PercentageField
from django.contrib.postgres.fields import ArrayField


class PlayerBadges(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="badge")
    badge = models.ForeignKey("players.Badge", on_delete=models.CASCADE)
    badge_level = models.ForeignKey("players.BadgeLevel", on_delete=models.CASCADE, null=True, blank=True)
    point = PercentageField()
    templates = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    assigned_by = models.ForeignKey("users.User", on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={"is_superuser": True})

    class Meta:
        unique_together = ("user", "badge", "badge_level")


class TemplateCache(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="badge_template_cache")
    badge = models.ForeignKey("players.Badge", on_delete=models.CASCADE)
    templates = ArrayField(models.CharField(max_length=255), null=True, blank=True)
