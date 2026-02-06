from common.models import CommonFields, TransactionFields
from django.db import models


class AdminSubscriptionTransaction(TransactionFields):
    # for the backup capture webhook
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="admin_transaction")


class AdminSubscription(CommonFields):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="admin_subscription",
        limit_choices_to={"user_role": "sub_admin"}
    )
    start_date = models.DateField()
    end_date = models.DateField()
    transaction = models.ForeignKey(
        AdminSubscriptionTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
