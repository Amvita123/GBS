from rest_framework import serializers
from ..models import *
from users.models import User
from common.services import human_readable_timesince


class FcmTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['id', 'token', 'device_type', 'os', 'browser']


class NotificationActionDetails(serializers.Serializer):
    def to_representation(self, instance):
        try:
            return {
                "destination": str(instance.action).replace("/", ''),
                "object_id": instance.objects_id,
                "user_id": instance.from_user.id if instance.from_user else "",
                "username": instance.from_user.get_full_name() if instance.from_user else "",
                "profile_pic": instance.from_user.profile_pic.url if instance.from_user and instance.from_user.profile_pic else ""
            }
        except Exception as e:
            return {
                "error": str(e)
            }


class NotificationSerializer(serializers.ModelSerializer):
    challenge = serializers.PrimaryKeyRelatedField(source="challenge.challenge_id", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "message", "challenge", "created_at", "is_action", )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['username'] = instance.from_user.username if instance.from_user else "Admin"
        if "challenge" not in representation:
            representation['challenge'] = ""
        else:
            try:
                if instance.challenge.is_accepted:
                    representation['status'] = "accepted"
                elif instance.challenge.is_accepted is False:
                    representation['status'] = "rejected"
                else:
                    representation['status'] = "pending"
            except Exception as e:
                print(e)

        representation['created_at'] = human_readable_timesince(instance.created_at)
        representation['action'] = NotificationActionDetails().to_representation(instance)

        return representation


class NotificationSendSerializer(serializers.Serializer):
    ACTION_CHOICES = [
        ("notification", "Notification"),
        ("share_post", "Share Post"),
    ]
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    message = serializers.CharField(required=False)
    object_id = serializers.CharField(required=False)
    to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_superuser=False, is_active=True)
    )

    def validate(self, attrs):
        errors = {}

        if attrs.get("action") == "share_post" and attrs.get("object_id") is None:
            errors['object_id'] = "post id is required to share post."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            if "action" in e.detail:
                e.detail["action"] = {
                    "error": "Invalid action. Choose one from the list.",
                    "valid_choices": [choice[0] for choice in self.ACTION_CHOICES]
                }
            raise e
