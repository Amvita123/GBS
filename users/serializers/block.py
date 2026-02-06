from rest_framework import serializers
from users.models import BlockUser


class BlockUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockUser
        fields = ("blocked",)
