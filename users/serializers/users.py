from rest_framework import serializers
from users.models import User, BlockUser, IdentityVerification
from players.api.serializers import ProfileSerializer as PlayerProfileSerializer
from players.models import Follow
import re
from coach.models import CoachType


class UserSerializer(serializers.ModelSerializer):
    biograph = serializers.CharField(required=True)
    is_blocked = serializers.SerializerMethodField(read_only=True)
    block_by_you = serializers.SerializerMethodField(read_only=True, method_name="is_current_user_blocked")
    coach_type = serializers.PrimaryKeyRelatedField(queryset=CoachType.objects.all(), write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id", 'first_name', "last_name", "email", "user_role", "username", "profile_pic", "biograph", "position", "school_name", "is_verified",
            "is_private", "is_blocked", "block_by_you", "phone_number", "dob", "coach_type", "is_identity_verified", "is_username_enable"
        ]

    def get_is_blocked(self, instance):
        try:
            if BlockUser.objects.filter(blocker=instance, blocked=self.context.get("request").user).exists():
                return True
        except:
            pass

        return False

    def is_current_user_blocked(self, instance):
        try:
            if BlockUser.objects.filter(blocked=instance, blocker=self.context.get("request").user).exists():
                return True
        except:
            pass
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_follow = Follow.objects.all()
        follower = user_follow.filter(following=instance)
        representation['follower'] = follower.count()
        representation['following'] = user_follow.filter(follower=instance).count()
        representation['profile_pic'] = instance.profile_pic.url if instance.profile_pic else ""

        if representation['user_role'] == "player":
            player_profile = PlayerProfileSerializer(instance.player_profile)
            representation['player_info'] = player_profile.data

        if representation['user_role'] != 'coach':
            del representation['position']
        else:
            representation['position'] = representation['position'].replace("_", " ")
            representation['coach_type'] = instance.coach_type.name if instance.coach_type else ""

        try:
           user = self.context.get("request").user
           representation['is_following'] = False
           if follower.filter(follower=user).exists():
               representation['is_following'] = True
        except:
            pass

        try:
            representation["verification_status"] = ""
            representation["parent_verified"] = ""
            if IdentityVerification.objects.filter(user=instance).exists():
                verification_obj = IdentityVerification.objects.filter(user=instance).latest("created_at")
                representation["verification_status"] = verification_obj.status

                if verification_obj.is_under is True:
                    transaction = verification_obj.verification_transactions.latest("created_at")
                    if transaction.status == "succeeded":
                        representation["parent_verified"] = verification_obj.parent_verified

        except Exception as e:
            print(f"{e}")
        return representation

    def get_is_following(self, instance):
        request = self.context.get("request")
        return True


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "confirm password does not match."})

        return attrs


class UserFollow(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("follower", "following", )
        read_only_fields = ["follower"]


class UserFollowerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ['id', "created_at", 'user']

    def get_user(self, obj):
        action = self.context.get("action")
        if action == "follower":
            user = obj.follower
        else:
            user = obj.following

        return UserSerializer(user, context={"request":
                                             self.context.get("request")}).data

