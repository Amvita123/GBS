from rest_framework import serializers
from event.models import EventFollower
from users.serializers import UserSerializer


class EventFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventFollower
        fields = ("event", )


class EventFollowUser(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventFollower
        fields = ("user", )

    def to_representation(self, instance):
        return UserSerializer(instance.user).data
