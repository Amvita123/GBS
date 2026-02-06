from rest_framework import serializers
from users.api.views import UserSerializer
from users.models import User
from players.models import Player as PlayerProfile, Sport, Position, PlayingStyle, SchoolGrade
from common.models import Skill
from notification.api.serializer import FcmTokenSerializer


class PlayerSignUp(UserSerializer):
    user_roles = (
        ("player", "player"),
    )
    # confirm_password = serializers.CharField()
    user_role = serializers.ChoiceField(choices=user_roles)
    school_name = serializers.CharField(required=True, )
    weight = serializers.FloatField(required=False,)
    height = serializers.FloatField(required=False, )
    position = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), required=False
    )
    sport = serializers.PrimaryKeyRelatedField(
        queryset=Sport.objects.all()
    )
    playing_style = serializers.PrimaryKeyRelatedField(
        queryset=PlayingStyle.objects.all(), required=False
    )

    fcm = FcmTokenSerializer(required=False)
    grade = serializers.PrimaryKeyRelatedField(
        queryset=SchoolGrade.objects.all(),
        required=False
    )

    class Meta(UserSerializer.Meta):
        user_fields = UserSerializer.Meta.fields
        fields = user_fields + ["password", "weight", "height",
                                "position", "sport", "playing_style", "school_name", "fcm", "grade", "platform"
                                ]

    def create(self, validated_data):
        # validated_data.pop("confirm_password")
        player_data = {
            "height": validated_data.pop("height") if validated_data.get("height") else None,
            "weight": validated_data.pop("weight") if validated_data.get("weight") else None,
            "sport": validated_data.pop("sport"),
            "grade": validated_data.pop("grade") if validated_data.get("grade") else None
        }
        if validated_data.get("position"):
            player_data["position"] = validated_data.pop("position")

        if validated_data.get("playing_style"):
            player_data["playing_style"] = validated_data.pop("playing_style")

        user = User.objects.create_user(
            is_active=False,
            password=validated_data.pop("password"),
            **validated_data
        )

        PlayerProfile.objects.create(
            user=user,
            **player_data
        )

        return user

    def validate(self, attrs):
        if attrs.get("position"):
            if not attrs.get("playing_style"):
                raise serializers.ValidationError({"playing_style": "Invalid playing style or does n't exists to selected position."})

            if attrs.get("position").id != attrs.get("playing_style").position.id:
                raise serializers.ValidationError({"playing_style": "Invalid style or does n't exists to selected position."})

        # if not attrs.get("phone_number"):
        #     raise serializers.ValidationError(
        #         {"phone_number": "This field is required.."})

        if "username" in attrs:
            attrs['username'] = attrs.get("username").lower()
        if "email" in attrs:
            attrs['email'] = attrs.get("email").lower()
        return attrs

    def to_internal_value(self, data):
        data = data.copy()
        if "email" in data:
            data["email"] = data["email"].lower()
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        # # validated_data.pop("confirm_password")
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.biograph = validated_data.get("biograph", instance.biograph)
        instance.profile_pic = validated_data.get("profile_pic", instance.profile_pic)
        instance.school_name = validated_data.get("school_name", instance.school_name)
        instance.is_private = validated_data.get("is_private", instance.is_private)
        instance.username = validated_data.get("username", instance.username)
        instance.dob = validated_data.get("dob", instance.dob)
        instance.is_username_enable = validated_data.get("is_username_enable", instance.is_username_enable)
        instance.save()

        player_profile = instance.player_profile
        player_profile.height = validated_data.get("height", player_profile.height)
        player_profile.weight = validated_data.get("weight", player_profile.weight)
        player_profile.grade =  validated_data.get("grade", player_profile.grade)

        player_profile.position = validated_data.get("position", player_profile.position)
        player_profile.playing_style = validated_data.get("playing_style", player_profile.playing_style)

        player_profile.save()

        return instance
