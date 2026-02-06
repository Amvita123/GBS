from django import forms
from users.models import User, ReferralOrganization
from django.core.validators import RegexValidator
from django.contrib.auth.models import Permission


class CreateSubAdminForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )

    user_role_choices = (
        ("sub_admin", "Sub Admin"),
        ("ar_staff", "AR Staff")
    )

    user_role = forms.ChoiceField(choices=user_role_choices)
    organization = forms.ModelChoiceField(
        queryset=ReferralOrganization.objects.all(),
        required=False
    )

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(
            content_type__app_label="users",
            codename__in=[
                "identity_verification",
                "edit_events",
                "view_revenue_share",
                "view_all_event",
            ]
        ),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = User
        fields = ("email", "first_name",  "last_name", "phone_number", "user_role", "organization", "permissions")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email



