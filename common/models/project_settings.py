from .common import CommonFields
from django.db import models


class ProjectSettings(CommonFields):
    player_verification = models.FloatField(default=0, help_text="The player's verification payment charge")
    coach_verification = models.FloatField(default=0, help_text="The coach's verification payment charge")
    organization_create = models.FloatField(default=0, help_text="The organization's creation payment charge")
    admin_subscription = models.FloatField(default=0,
                                           help_text="The sub admin's or external subscription payment charge")
    discount_code_limit = models.PositiveIntegerField(default=0, help_text="The discount code limit")


class AppRelease(CommonFields):
    PLATFORM_CHOICES = (
        ("ANDROID", "Android"),
        ("IOS", "iOS"),
    )
    platform = models.CharField(
        max_length=10,
        choices=PLATFORM_CHOICES
    )

    app_version = models.CharField(
        max_length=20,
        help_text="User-visible version, e.g. 1.2.3"
    )

    build_number = models.PositiveIntegerField(
        help_text="Internal build number (Android versionCode / iOS build)"
    )

    min_supported_build = models.PositiveIntegerField(
        help_text="Minimum allowed build number"
    )

    force_update = models.BooleanField(
        default=False,
        help_text="If true, app must update to continue"
    )

    release_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("platform", "build_number")
        ordering = ["-build_number"]

    def __str__(self):
        return f"{self.platform} v{self.app_version} ({self.build_number})"
