from common.models import CommonFields
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class FeedBadges(CommonFields):
    feed = models.ForeignKey("common.Feed", on_delete=models.CASCADE, related_name="feed_badge")
    badge = models.ForeignKey("players.Badge", on_delete=models.CASCADE)

    def clean(self):
        if self.pk:
            if self.feed.badge.count() >= 3:
                raise ValidationError("A post can have at most 3 badge.")

    def save(self, *args, **kwargs):
        # self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.feed.user.get_username()} - {self.badge.name}"

    @property
    def ratings(self):
        return [rete_badge for rete_badge in self.rating.all()] if hasattr(self, 'rating') else []


class FeedBadgeRating(CommonFields):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="rated_by"
    )  # limit_choices_to=models.Q(user_role="fan") | models.Q(user_role="coach")
    rate_badge = models.ForeignKey(
        "players.FeedBadges", on_delete=models.CASCADE,
        related_name="rating"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        unique_together = ("user", "rate_badge")


