from common.models import CommonFields
from django.db import models
from .plans import EventPlan


def get_default_plan():
    """Return the default Free plan (create if not exists)."""
    plan, _ = EventPlan.objects.get_or_create(
        name="free",
        defaults={
            "price": 0,
            "description": "Free plan",
            "features": [],
        },
    )
    return plan.id


class EventTransaction(CommonFields):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="event_transaction",
        null=True, blank=True
    )
    event_plan = models.ForeignKey(
        "event.EventPlan",
        on_delete=models.SET_DEFAULT,
        default=get_default_plan,
        related_name="transactions"
    )

    event = models.ForeignKey(
        "event.Event",
        on_delete=models.SET_NULL,
        related_name="event_transactions",
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





