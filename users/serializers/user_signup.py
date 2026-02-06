from rest_framework import serializers
from users.models import User
from .users import UserSerializer
from players.models import Player as PlayerProfile
from notification.api.serializer import FcmTokenSerializer
import phonenumbers


class UserSignUpSerializer(UserSerializer):
    user_roles = (
        ("fan", "fan"),
        ("coach", "coach"),
    )

    Position_Choice = (
        ('trainer', 'trainer'),
        ('manager', 'manager'),
        ('recruiter', 'recruiter'),
        ('head_coach', 'head coach'),
        ('player_development', 'player development'),
        ('scouting', 'scouting'),
        ('video_coordinator', 'video coordinator'),
        ('others', 'others')
    )

    # confirm_password = serializers.CharField()
    user_role = serializers.ChoiceField(choices=user_roles)
    position = serializers.ChoiceField(choices=Position_Choice, required=False)
    school_name = serializers.CharField(required=False)
    fcm = FcmTokenSerializer(required=False)

    def to_internal_value(self, data):
        data = data.copy()
        if "email" in data:
            data["email"] = data["email"].lower()
        return super().to_internal_value(data)

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ['user_role', 'position', "password", "fcm", "coach_type", "platform"]

    def validate(self, attrs):
        user_role = attrs.get("user_role")
        # phone_number = attrs.get('phone_number')

        errors = {}

        if user_role == 'coach':
            position = attrs.get("position")
            if not position:
                errors['position'] = "This field required for coaches."
        elif user_role == 'fan':
            if 'position' in attrs:
                del attrs['position']

        # if not phone_number:
        #     errors['phone_number'] = "This field is required."

        if errors:
            raise serializers.ValidationError(errors)

        # del attrs['confirm_password']
        return attrs


class OtpVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    otp = serializers.IntegerField(min_value=100000, max_value=999999,
                                   error_messages={
                                       'min_value': 'OTP must be a 6-digit number.',
                                       'max_value': 'OTP must be a 6-digit number.',
                                       'invalid': 'Invalid OTP. Please enter a valid 6-digit number.'
                                   })

    def validate(self, attrs):
        email = attrs.get("email").lower()
        user = User.objects.filter(email=email)
        if user.exists() is True:
            attrs['user'] = user.first()
        else:
            raise serializers.ValidationError({"email": "email does not exists"})

        return attrs
