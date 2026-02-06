from django import forms
from notification.models import Notification, PushNotification
from users.models import User


class NotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user_type"].choices = [
                                               (value, label) for value, label in User.user_roles if value != "admin"
                                           ] + [("event", "Event")]

    user_type = forms.ChoiceField(choices=User.user_roles)

    class Meta:
        model = Notification
        fields = ["title", "message", "user_type"]


class PushNotificationForm(forms.ModelForm):
    class Meta:
        model = PushNotification
        fields = ("title", "message", "to", "event", "schedule")
