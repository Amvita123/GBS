from django.db import models
from common.models import CommonFields
from django.urls import reverse
from event.services import generate_qr_code
from django.contrib.sites.models import Site


class Event(CommonFields):
    EVENT_TYPE_CHOICES = (
        ("ar", "ar"),
        ("solo", "solo"),
        ("premium", "premium"),
        ("free", "free"),
    )
    name = models.CharField(max_length=255)
    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True,
                             limit_choices_to=models.Q(user_role='admin') | models.Q(user_role='coach') | models.Q(
                                 user_role='sub-admin'))
    logo = models.ImageField(upload_to="event/", null=True, blank=True,
                             )  # validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic'])]
    booking_link = models.JSONField(default=dict, blank=True)
    date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    event_type = models.CharField(max_length=100, choices=EVENT_TYPE_CHOICES, default="free")
    qr_code = models.ImageField(upload_to="ticket_qr/", blank=True, null=True)
    teams = models.ManyToManyField("event.Team", related_name="matches", blank=True)
    rosters = models.ManyToManyField("coach.Roster", related_name="event_roster", blank=True)
    roster_win = models.ForeignKey("coach.Roster", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="event_roster_win")
    sub_admins = models.ManyToManyField("users.User", related_name="assigned_events", blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("event-detail", args=[self.pk])

    def save(
            self,
            *args,
            **kwargs
    ):
        super().save(*args, **kwargs)

        if not self.qr_code:
            current_site = Site.objects.get_current()
            domain = current_site.domain
            data = f"{domain}/app/event_checkIn/{self.id}"
            filename, qr_file = generate_qr_code(data, f"event_{self.pk}.png")
            self.qr_code.save(filename, qr_file, save=False)
            super().save(update_fields=["qr_code"])
