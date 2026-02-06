from rest_framework import serializers
from users.serializers import UserSerializer
from chatapp.models import ChallengeGroupChat


class ChallengeGroupSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        players = instance.first_squad.players.all() | instance.second_squad.players.all()

        return {
            "title": f"{instance.first_squad.name} vs {instance.second_squad.name}",
            "challenge_id": instance.challenge_id,
            "result_date": instance.result_date,
            "players": UserSerializer(players, many=True).data
        }


class ChallengeChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeGroupChat
        fields = ("id", "message", "is_edit", "challenge", )
        extra_kwargs = {
            "challenge": {"write_only": True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = {
            "fullname": instance.users.get_full_name(),
            "username": instance.users.username,

        }
        return representation
