from django.db import models
from common.models import CommonFields
from django.contrib.postgres.fields import ArrayField


class EventPlan(CommonFields):
    PLAN_CHOICES = [
        ("premium", "Premium"),
        ("solo", "Solo"),
        ("ar_staff", "AR Staff"),
        ("free", "Free"),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    features = ArrayField(models.CharField(max_length=255))

    class Meta:
        ordering = ['name']

