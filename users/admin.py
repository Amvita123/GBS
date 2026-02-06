from django.contrib import admin
from .models import User, IdentityVerification, AthleteTypes, DocumentType, VerificationTransaction
from import_export.admin import ImportExportModelAdmin
from django.utils.html import mark_safe
from django.contrib.auth.models import Permission


class UserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['username', "email", "user_role", "id", "profile_pic_display"]
    list_filter = ["user_role", "player__position"]
    ordering = ['-date_joined']

    def profile_pic_display(self, obj):
        if obj.profile_pic:
            return mark_safe(f'<img src="{obj.profile_pic.url}" width="50" height="50" />')
        return "No Image"

    profile_pic_display.short_description = 'Profile Picture'


class VerificationTransactionInline(admin.TabularInline):
    model = VerificationTransaction
    extra = 0
    can_delete = False
    show_change_link = True

    readonly_fields = (
        "id",
        "user",
        "amount",
        "currency",
        "status",
        "created_at",
    )

    fields = readonly_fields


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "legal_full_name",
        "user",
        "athlete_type",
        "dob",
        "is_under",
        "status",
        "parent_verified",
        "is_active",
        "created_at",
    )

    list_filter = (
        "status",
        "parent_verified",
        "is_under",
        "athlete_type",
        "document_type",
        "school_document_type",
        "created_at",
    )

    search_fields = (
        "legal_full_name",
        "user__email",
        "user__username",
        "parent_legal_name",
        "parent_email",
        "refer_by",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")
    inlines = [VerificationTransactionInline]

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "user",
                "legal_full_name",
                "photo",
                "athlete_type",
                "dob",
                "is_under",
            )
        }),
        ("Identity Documents", {
            "fields": (
                "document_type",
                "identity_img",
            )
        }),
        ("School Verification", {
            "fields": (
                "school_document_type",
                "school_document",
            )
        }),
        ("Parent / Guardian Details", {
            "fields": (
                "parent_legal_name",
                "parent_email",
                "parent_phone_number",
                "parent_verified",
            ),
            "classes": ("collapse",),
        }),
        ("Verification Status", {
            "fields": (
                "status",
                "remark",
                "reject_reason",
            )
        }),
        ("Reference & Meta", {
            "fields": (
                "refer_by",
                "created_at",
                "updated_at",
                "is_active"
            )
        }),
    )

    list_display_links = ("legal_full_name", "user")

admin.site.register(User, UserAdmin)
admin.site.register(AthleteTypes)
admin.site.register(DocumentType)
admin.site.register(Permission)
