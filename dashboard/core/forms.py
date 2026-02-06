from django import forms
from users.models import User
from django.core.exceptions import ValidationError
from common.models import Setting, ProjectSettings
from django.db.models import Q
from players.models import Sport
from users.models.discount_management import DiscountCode


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
        try:
            user = User.objects.get(
                Q(is_superuser=True) | Q(user_role="sub_admin") | Q(user_role="admin") | Q(user_role="ar_staff"),
                email__iexact=email)
        except User.DoesNotExist:
            raise ValidationError("This email does not exist in our records.")

        return user.username


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ["terms_conditions", "privacy_policy"]


class AdminProfile(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    profile_pic = forms.ImageField(required=False)


class SetPassword(forms.Form):
    new_password = forms.CharField(max_length=30)
    confirm_new_password = forms.CharField(max_length=30)


class ProjectSettingsForm(forms.ModelForm):
    class Meta:
        model = ProjectSettings
        fields = [
            "player_verification",
            "coach_verification",
            "organization_create",
            "admin_subscription",
        ]


class SportForm(forms.ModelForm):
    class Meta:
        model = Sport
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter sport name'
            })
        }


class DiscountCodeForm(forms.ModelForm):
    class Meta:
        model = DiscountCode
        fields = ["code_value", "usage_limit", "code_identifier"]

        widgets = {
            "code_value": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter code value", "max": 100, "min": 0,
                       "required": True}),
            "usage_limit": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "eg. 20 usage", "required": True}),
            "code_identifier": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter identifier", "id": "code_identifier"}),
        }

    def clean_code_value(self):
        value = self.cleaned_data["code_value"]
        if value > 100:
            raise forms.ValidationError("Discount cannot exceed 100%")
        return value

    def clean_code_identifier(self):
        code = self.cleaned_data.get("code_identifier")
        if not code:
            return code
        code = code.upper()
        if len(code) < 8:
            raise ValidationError("Code must be at least 8 characters")
        return code
