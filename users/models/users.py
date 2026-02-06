import uuid
import phonenumbers

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from .user_manager import UserManager


def validate_phone_number(value):
    if not value.startswith('+'):
        value = '+' + value

    try:
        number = phonenumbers.parse(value, None)

        if not phonenumbers.is_possible_number(number):
            raise ValidationError("Phone number is not possible.")
        if not phonenumbers.is_valid_number(number):
            raise ValidationError("Phone number is not valid.")

    except phonenumbers.NumberParseException:
        raise ValidationError("Invalid phone number format. Use +<countrycode><number> (e.g. +919876543210).")


class User(AbstractUser):
    @property
    def player_profile(self):
        return self.player if hasattr(self, 'player') else None

    gender_choice = (
        ("male", "male"),
        ("female", "female"),
        ("others", "others")
    )
    user_roles = (
        ("player", "player"),
        ("fan", "fan"),
        ("coach", "coach"),
        ("admin", "admin"),
        ("sub_admin", "Sub Admin"),
        ("ar_staff",  "AR Staff")
    )

    coach_position_Choice = (
        ('trainer', 'Trainer'),
        ('manager', 'Manager'),
        ('recruiter', 'Recruiter'),
        ('head_coach', 'Head Coach'),
        ('player_development', 'Player Development'),
        ('scouting', 'Scouting'),
        ('video_coordinator', 'Video Coordinator'),
        ('others', 'Others')
    )

    auth_type = (
        ("EMAIL", "EMAIL"),
        ("GOOGLE", "GOOGLE"),
        ("APPLE", "APPLE")
    )

    id = models.CharField(primary_key=True, default=uuid.uuid4, unique=True, editable=False, max_length=255)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_set_password = models.BooleanField(default=True)
    user_role = models.CharField(choices=user_roles, max_length=15)
    profile_pic = models.ImageField(upload_to="profile", null=True, blank=True,
                                    validators=[
                                        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic'])]
                                    )
    biograph = models.TextField(null=True, blank=True)
    school_name = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    position = models.CharField(max_length=200, null=True, blank=True, help_text="for coach only",
                                choices=coach_position_Choice)  # this is for coach only
    is_private = models.BooleanField(default=False)
    auth_type = models.CharField(choices=auth_type, default="EMAIL", max_length=15)
    phone_number = models.CharField(
        max_length=15, unique=True, null=True, blank=True,
        validators=[
            validate_phone_number
        ]
    )
    dob = models.DateField(null=True, blank=True)
    coach_type = models.ForeignKey("coach.CoachType", on_delete=models.CASCADE, null=True, blank=True)  # for coach only
    platform = models.CharField(max_length=15, null=True, blank=True)
    is_identity_verified = models.BooleanField(default=False)
    is_username_enable = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["first_name", "last_name", "email", "password"]
    USERNAME_FIELD = "username"
    objects = UserManager()
