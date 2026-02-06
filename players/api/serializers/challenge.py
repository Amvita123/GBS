from rest_framework import serializers
from players.models import Challenge, Squad
from .squad import SquadSerializer
from datetime import datetime


class ChallengeSerializer(serializers.ModelSerializer):
    first_squad = SquadSerializer(read_only=True)
    second_squad = SquadSerializer(read_only=True)
    squad = serializers.SlugRelatedField(
        queryset=Squad.objects.all(),
        write_only=True,
        slug_field='squad_id'
    )

    class Meta:
        model = Challenge
        fields = ("challenge_id", "first_squad", "second_squad", "result_date", "status", "squad", "winner", "point_first_squad", "point_second_squad")
        extra_kwargs = {
            "challenge_id": {"read_only": True},
            "status": {"read_only": True},
            "point_second_squad": {"read_only": True},
            "point_first_squad": {"read_only": True},
            "winner": {"read_only": True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['result_date'] = instance.result_date.strftime("%d-%b,%Y")
        representation["participant"] = instance.first_squad.players.all().count() + instance.second_squad.players.all().count()
        if instance.winner:
            representation['winner'] = instance.winner.name
        return representation

    def validate(self, attrs):
        result_date = attrs.get("result_date")
        if result_date < datetime.now().date():
            raise serializers.ValidationError({"result_date": "Invalid date. Please select an upcoming or future date."})

        return attrs


class ChallengeActionSerializer(serializers.Serializer):
    action_choice = (
        ("accept", "accept"),
        ("reject", "reject")
    )
    action = serializers.ChoiceField(choices=action_choice)
    challenge_id = serializers.IntegerField()
