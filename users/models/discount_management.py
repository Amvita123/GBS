from django.db import models
from common.models import CommonFields
import random
import string
from users.models.users import User


def generate_discount_code():
    characters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=5))
    return characters + numbers


class DiscountCode(CommonFields):
    code_identifier = models.CharField(max_length=8, unique=True, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    current_usage = models.PositiveIntegerField(default=0)
    code_value = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):

        if not self.code_identifier:
            self.code_identifier = generate_discount_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.code_identifier)


class DiscountCodeUsage(CommonFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discount = models.ForeignKey(DiscountCode, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "discount")


