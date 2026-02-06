from django.db import models
import uuid


class CustomModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class CommonFields(models.Model):
    id = models.CharField(max_length=255, primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    master_objects = models.Manager()
    objects = CustomModelManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    # def delete(self, using=None, keep_parents=False):
    #     self.is_deleted = True
    #     self.save()


class Setting(CommonFields):
    terms_conditions = models.TextField()
    privacy_policy = models.TextField()

    def save(self, *args, **kwargs):
        if Setting.objects.exists() and not self.pk:
            raise ValueError('only one privacy policy & terms conditions')
        super().save(*args, **kwargs)


class TransactionFields(CommonFields):
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

    class Meta:
        abstract = True

