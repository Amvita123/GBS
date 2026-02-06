from rest_framework import serializers
from players.models import Squad, SquadStructure
from users.serializers.users import UserSerializer
from users.models import User


class SquadSerializer(serializers.ModelSerializer):
    # created_by = UserSerializer(read_only=True)
    # players = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.filter(user_role='player'),
    #     many=True,
    #     error_messages={
    #         'does_not_exist': 'Invalid player selected. Only players can be added.',
    #         'incorrect_type': 'Invalid player data type.'
    #     }
    # )
    structure = serializers.PrimaryKeyRelatedField(
        queryset=SquadStructure.objects.all(),
        write_only=True,
    )
    create_new = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = Squad
        fields = ("id", "squad_id", "name", "win", "loss", "logo", "structure", "players", "create_new", )

    def validate(self, attrs):
        players = attrs.get("players")
        if players is not None and len(players) > 4:
            raise serializers.ValidationError({"players": "You can only have a maximum of 4 players."})
        elif players and len(players) < 4:
            raise serializers.ValidationError({"players": "please select more players."})
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        players = list(UserSerializer(instance.players, many=True).data)
        representation['structure'] = instance.structure.structure
        for player in players:
            if player['username'] == instance.created_by.username:
                player['is_admin'] = True
            else:
                player['is_admin'] = False

        representation['players'] = players

        if representation['logo'] is None:
            representation['logo'] = ""
        else:
            representation['logo'] = instance.logo.url

        return representation

    def update(self, instance, validated_data):
        print("---he")
        instance.name = validated_data.get("name", instance.name)
        instance.structure = validated_data.get("structure", instance.structure)
        players = validated_data.get("players", [])

        for player in instance.players.all().exclude(id=instance.created_by.id):
            instance.players.remove(player)

        for player in players:
            instance.players.add(player)

        if "logo" in validated_data:
            instance.logo = validated_data["logo"]

        instance.save()

        if instance.players.count() == 0:
            instance.delete()
            return False
        return instance

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #
    #     request = self.context.get('request', None)
    #     if request and request.method == 'PUT':
    #         for field in self.fields.values():
    #             field.required = True
    #             field.allow_null = False


class SquadStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SquadStructure
        fields = ["id", "structure", "rating", "position_1", "position_2", "position_3", "position_4", "position_5"]


class SquadLeaderboardSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField()
    leader = serializers.CharField(source='created_by')
    win_percentage = serializers.FloatField()
    players_count = serializers.IntegerField()

    class Meta:
        model = Squad
        fields = [
            'rank',
            'id',
            'name',
            'leader',
            'win',
            'loss',
            'win_percentage',
            'players_count',
            "logo"
        ]

