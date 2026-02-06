from django import forms
from players.models import Player, Badge, SchoolGrade


class JerseyNumberForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['jersey_number']

    def clean_jersey_number(self):
        jersey_number = self.cleaned_data.get('jersey_number')
        if jersey_number is None or jersey_number <= 0:
            raise forms.ValidationError("Jersey number must be a positive integer.")
        return jersey_number


class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = ("name", "description", "ranking", "weight")


class GradeForm(forms.ModelForm):
    class Meta:
        model = SchoolGrade
        fields = ['name']

