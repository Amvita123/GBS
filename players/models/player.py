from django.db import models
from common.models import CommonFields
from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class PercentageField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_digits', 5)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('default', 50.00)
        kwargs.setdefault('validators', [
            MinValueValidator(0),
            MaxValueValidator(100),
        ])
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_digits"]
        del kwargs["decimal_places"]
        del kwargs["default"]
        return name, path, args, kwargs


def validate_required(value):
    if value is None:
        raise ValidationError("this field is required.")


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rating = models.PositiveIntegerField(validators=[validate_required], null=True, )

    def __str__(self):
        return self.name


class Player(CommonFields):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, limit_choices_to={"user_role": "player"}, related_name="player")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True, blank=True)
    weight = models.FloatField(help_text="pound", null=True, blank=True)
    height = models.FloatField(help_text="foot&inch", null=True, blank=True)
    sport = models.ForeignKey("players.Sport", on_delete=models.CASCADE, null=True, blank=True)
    playing_style = models.ForeignKey(
        "players.PlayingStyle", on_delete=models.CASCADE,
        null=True, blank=True
    )
    overall_rating = PercentageField(editable=False)
    jersey_number = models.IntegerField(null=True, blank=True, unique=True)
    grade = models.ForeignKey("players.SchoolGrade", on_delete=models.CASCADE, null=True, blank=True)


class PlayingStyle(models.Model):
    title = models.CharField(max_length=255)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True)
    archetype_rating = models.PositiveIntegerField(null=True, validators=[validate_required])

    def __str__(self):
        return f"{self.title} -- {self.position.name}"

    class Meta:
        unique_together = ("title", "position",)


class Badge(CommonFields):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    ranking = models.PositiveIntegerField(null=True, validators=[validate_required])
    is_admin_assignable = models.BooleanField(default=True)
    weight = models.IntegerField(null=True)
    icon = models.FileField(upload_to='badges/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("ranking", )


levels = (
    ("ice_white", "Ice White"),
    ("blue", "Blue"),
    ("green", "Green"),
    ("bronze", "Bronze"),
    ("silver", "Silver"),
    ("gold", "Gold"),
    ("purple", "Purple"),
    ("red", "Red")
)


class BadgesCheckList(models.Model):
    name = models.CharField(max_length=50, choices=levels)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="No. of star",
        null=True
    )
    weight = models.IntegerField(
        help_text="No of rated people",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        null=True
    )
    auto_assignable = models.BooleanField(
        default=True,
        help_text="If admin assignable make sure this is unchecked. \n If you are adding admin assignable put weight & rating_no value 1."
    )

    class Meta:
        unique_together = ("name", "weight", "rating")

    def __str__(self):
        return f"{self.name} - {self.rating}"


class BadgeLevel(models.Model):
    name = models.CharField(max_length=50, choices=levels, null=True)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="badge_level")
    icon = models.ImageField(
        upload_to="badge_icon/",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', "heic"])
        ],
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.badge.name}"

    @staticmethod
    def level_points():
        level_points = {
            "yellow": 70,
            "orange": 80,
            "green": 90,
            "bronze": [
                75, 76, 77, 78, 79
            ],
            "silver": [85, 86, 87, 88, 89],
            "gold": [95, 96, 97, 98, 99]
        }
        return level_points


class BadgeLevelTemplate(models.Model):
    title = models.CharField(max_length=255)
    badge_level = models.ForeignKey(BadgeLevel, on_delete=models.CASCADE, related_name="badge_template")

    def __str__(self):
        return f"{self.title} - {self.badge_level.name}"
