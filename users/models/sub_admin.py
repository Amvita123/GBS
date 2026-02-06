from django.db import models
from common.models import CommonFields


# class Permission(models.Model):
#     permission_keys = (
#         ("identity_verification", "Identity Verification")
#     )
#     title = models.CharField(max_length=255, unique=True)
#     is_active = models.BooleanField(default=True)
#     is_enabled = models.BooleanField(default=True)
#
#
# class SubAdminPreference(CommonFields):
#     EVENT_TYPE_CHOICES = (
#         ("ar", "ar"),
#         ("solo", "solo"),
#         ("premium", "premium"),
#         ("all", "all"),
#     )
#     user = models.OneToOneField("users.User", on_delete=models.CASCADE, limit_choices_to={"user_role": "sub-admin"}, related_name="sub_admin")
#     created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name="sub_admin_created_by")
#     event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
#     permissions = models.ManyToManyField(Permission, blank=True)

class ARPermission(models.Model):
    class Meta:
        managed = True
        permissions = [
            ("identity_verification", "Can verify identity"),
            ("edit_events", "Can edit or add events"),
            ("view_revenue_share", "Can view revenue share report"),
            ("view_all_event", "Can manage all events (AR Staff full access)"),
        ]
