from rest_framework import serializers
from users.models import User
from django.db.models import Q
from notification.api.serializer import FcmTokenSerializer


class SignInSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    fcm = FcmTokenSerializer(required=False)

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(Q(email=email.lower()) | Q(username=email))
        if user.exists() is False:
            raise serializers.ValidationError({"email": "We couldn't find an account associated with this email or username."})
        # elif user.first().is_active is False:
        #     raise serializers.ValidationError({"email": "Your account is not active yet please verify email."})
        usr = user.first()
        # if user.user_role in ["admin", "sub_admin", "ar_staff"]:
        #     raise serializers.ValidationError({
        #         "email": f"You are unable to log in to the app because this email is linked to an {user.user_role.replace('_', ' ')} account."
        #     })
        attrs['user'] = usr
        return attrs


class ForgetPassword(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(email=email)
        if user.exists() is False:
            raise serializers.ValidationError({"email": "We couldn't find an account associated with this email."})
        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(email=email)
        if user.exists() is False:
            raise serializers.ValidationError({"email": "We couldn't find an account associated with this email."})

        new_password = attrs.get("new_password")
        confirm_new_password = attrs.get("confirm_new_password")

        if new_password != confirm_new_password:
            raise serializers.ValidationError({"confirm_new_password": "confirm password does not match."})

        attrs['user'] = user.first()
        return attrs


class SocialAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
    PLATFORM_CHOICES = [
        ("Google", 'Google'),
        ("Apple", 'Apple'),
    ]
    platform = serializers.ChoiceField(choices=PLATFORM_CHOICES)
    user_roles = (
        ("player", "player"),
        ("fan", "fan"),
        ("coach", "coach"),
    )
    user_role = serializers.ChoiceField(choices=user_roles, required=False)
    fcm = FcmTokenSerializer(required=False)

