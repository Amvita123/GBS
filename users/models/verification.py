from django.db import models
from common.models import CommonFields, TransactionFields
import os


class AthleteTypes(models.Model):
    title = models.CharField(max_length=150)

    def __str__(self):
        return self.title


class DocumentType(models.Model):
    title = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.title


class SchoolDocument(CommonFields):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class IdentityVerification(CommonFields):
    legal_full_name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="verification_photo/", null=True, blank=True)
    athlete_type = models.ForeignKey(AthleteTypes, on_delete=models.CASCADE, null=True, blank=True)
    dob = models.DateField()
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, null=True, blank=True)
    identity_img = models.FileField(upload_to="verification_identity")
    is_under = models.BooleanField(default=False)

    parent_legal_name = models.CharField(max_length=150, null=True, blank=True)
    parent_email = models.EmailField(null=True, blank=True)
    parent_phone_number = models.CharField(max_length=15, null=True, blank=True)

    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("accept", "Accept"),
            ("reject", "Reject"),
            ("expired", "Expired"),
            ("expiring", "Expiring")
        ],
        default="pending"
    )
    parent_verified = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("accept", "Accept"),
            ("reject", "Reject"),
        ],
        default="pending"
    )

    remark = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    reject_reason = models.JSONField(default=list, null=True, blank=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="verification")
    refer_by = models.CharField(max_length=255, null=True, blank=True)
    school_document_type = models.ForeignKey(SchoolDocument, on_delete=models.SET_NULL, null=True, blank=True)
    school_document = models.ImageField(upload_to="verification_school/", null=True, blank=True)
    discount = models.ForeignKey(
        "users.DiscountCode",
        on_delete=models.SET_NULL,
        null=True, blank=True
    )


    def is_school_document_image(self):
        return self.school_document.name.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif', '.webp')
        )

    @property
    def is_identity_pdf(self):
        return os.path.splitext(self.identity_img.name)[1].lower() == ".pdf"


class VerificationTransaction(TransactionFields):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="verification_transaction",
        null=True, blank=True
    )

    verification = models.ForeignKey(
        IdentityVerification,
        on_delete=models.SET_NULL,
        related_name="verification_transactions",
        null=True, blank=True
    )

class ReferralOrganization(CommonFields):
    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField("users.User", related_name="sub_admin_org", blank=True)
