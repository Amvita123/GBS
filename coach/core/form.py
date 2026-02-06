from django import forms
from coach.models import CoachType, RosterGrade


class CoachTypeForm(forms.ModelForm):
    class Meta:
        model = CoachType
        fields = ["name"]


class RosterGradeForm(forms.ModelForm):
    class Meta:
        model = RosterGrade
        fields = ["name"]
