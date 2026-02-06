from django.forms import ModelForm
from event.models import Event, EventRules, EventPlan, Team
from django import forms
from django.core.validators import FileExtensionValidator


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ["name", "logo", "booking_link", "date", "end_date", "description", "event_type", "location"]

    def clean_booking_link(self):
        data = self.cleaned_data.get("booking_link")
        if not data:
            raise forms.ValidationError("This field is required.")
        return data


class EventRulesForm(ModelForm):
    class Meta:
        model = EventRules
        fields = ['text']


class EventRuleForm(ModelForm):
    class Meta:
        model = EventPlan
        fields = ["name", "description", "price", "features"]

    def clean_features(self):
        features = self.cleaned_data.get("features")

        if not isinstance(features, (list, tuple)):
            raise forms.ValidationError("Features must be a list.")

        cleaned = [f.strip() for f in features if f.strip()]
        if not cleaned:
            raise forms.ValidationError("Please provide at least one feature.")
        return cleaned


class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name']


class UploadCsvForm(forms.Form):
    file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )

class AssignSubAdminForm(forms.Form):
    sub_admin_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False
    )