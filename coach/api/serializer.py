from rest_framework import serializers
from users.models import User
from players.models import Squad
from coach.models import *
from players.api.serializers import SportSerializer
from users.serializers import UserSerializer
from notification.models import Notification
from django.db.models import Q
from event.models import Event
from datetime import datetime


class OneToOneSimulationSerializer(serializers.Serializer):
    player_1 = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_role="player")
    )
    player_2 = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_role="player")
    )


class FiveToFiveSimulationSerializer(serializers.Serializer):
    queryset = Squad.objects.all()
    squad_1 = serializers.PrimaryKeyRelatedField(
        queryset=queryset
    )

    squad_2 = serializers.PrimaryKeyRelatedField(
        queryset=queryset
    )


class FiveTOFivePlayerSimulation(serializers.Serializer):
    players_group_1 = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_role="player"),
        many=True,
    )

    players_group_2 = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_role="player"),
        many=True
    )

    def validate_players_group_1(self, value):
        return self._validate_players_group(value, group_name="Group 1")

    def validate_players_group_2(self, value):
        return self._validate_players_group(value, group_name="Group 2")

    def _validate_players_group(self, value, group_name="Players"):
        limit = 5

        if len(value) > limit:
            raise serializers.ValidationError(f"You can select up to {limit} players only in {group_name}.")

        if len(value) < limit:
            raise serializers.ValidationError(f"You must select exactly {limit} players in {group_name}.")

        if len(set(value)) != len(value):
            raise serializers.ValidationError(f"Duplicate players are not allowed in {group_name}.")

        return value

    def validate(self, data):
        group_1 = set(data.get('players_group_1', []))
        group_2 = set(data.get('players_group_2', []))

        if group_1 & group_2:
            raise serializers.ValidationError({
                "detail": "Players cannot be in both Group 1 and Group 2."
            })

        return data


class CoachTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachType
        fields = ["id", "name"]


class RosterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roster
        fields = ["id", "name", "organization", "is_active", "created_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['organization'] = instance.organization.name
        representation['total_players'] = instance.roster_player.count()
        representation['wins'] = 0
        representation['loses'] = 0
        return representation


class RosterSerializer(serializers.ModelSerializer):
    coach = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_role="coach"),
        many=True,
        required=False,
        write_only=True
    )
    players = serializers.SerializerMethodField()
    coaches = serializers.SerializerMethodField(method_name="get_coaches")
    player = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_role="player"),
        write_only=True,
        many=True,
        required=False
    )

    class Meta:
        model = Roster
        fields = ["id", "name", "organization", "is_active", "created_at", "coach", "coaches", "players", "player",
                  "grade"]

    def validate(self, attrs):
        # request = self.context.get("request")
        coaches = attrs.get("coach")
        if len(coaches) > 4:
            raise serializers.ValidationError({"coaches": "You can not select more than 4 coaches."})
        return attrs

    def get_players(self, obj):
        result = []
        player = self.context.get("player")
        roster_players_obj = obj.roster_player.all()
        roster_players_obj = sorted(
            roster_players_obj,
            key=lambda rp: 0 if rp.player == player else 1
        )
        for player_instance in roster_players_obj:
            serialize = UserSerializer(player_instance.player)
            data = serialize.data
            data['jersey_number'] = player_instance.jersey_number
            data['position'] = player_instance.position
            result.append(data)

        return result

    def get_coaches(self, obj):
        result = []
        roster_coaches_obj = obj.roster_coach.all()
        for coach_instance in roster_coaches_obj:
            serialize = UserSerializer(coach_instance.coach)
            data = serialize.data
            data['jersey_number'] = coach_instance.jersey_number
            # data['position'] = coach_instance.position
            result.append(data)

        return result

    def create(self, validated_data):
        roster = Roster.objects.create(
            name=validated_data['name'],
            organization=validated_data.get("organization"),
            grade=validated_data.get("grade")
        )
        return roster

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['organization'] = instance.organization.name
        representation['sport'] = instance.organization.sport.name
        representation['logo'] = instance.organization.logo.url if instance.organization.logo else ""
        representation['total_players'] = instance.roster_player.count()
        representation['wins'] = 0
        representation['loses'] = 0
        return representation


class InvitePlayerSerializer(serializers.ModelSerializer):
    roster = serializers.PrimaryKeyRelatedField(
        queryset=Roster.objects.all()
    )
    class Meta:
        model = InvitePlayer
        fields = ["id", "roster", "name", "email", "phone_number"]


class InviteAppPlayerSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(Q(user_role="player") | Q(user_role="coach"))
    )
    roster = serializers.PrimaryKeyRelatedField(
        queryset=Roster.objects.all()
    )


class OrganizationRosterSerializer(serializers.ModelSerializer):
    players_count = serializers.SerializerMethodField()

    class Meta:
        model = Roster
        fields = ["id", "name", "created_at", "players_count"]

    def get_players_count(self, obj):
        return obj.roster_player.all().count()

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     representation['total_players'] = len(Roster.players)
    #     return representation


class EventSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'name', "logo", 'date', 'status', 'description', "location", "event_type", "is_active"]

    def get_status(self, obj):
        if obj.date < datetime.now():
            return "completed"
        else:
            return "upcoming"


class OrganizationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name"]


class OrganizationSerializer(serializers.ModelSerializer):
    roster = OrganizationRosterSerializer(read_only=True, many=True, )

    class Meta:
        model = Organization
        fields = ["id", "name", "logo", "sport", "biograph", "created_at", "roster"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.sport:
            representation["sport"] = SportSerializer(instance.sport).data
        else:
            representation["sport"] = None

        rosters = instance.roster.all()
        players, coaches = [], []
        # roster players
        for roster in rosters:
            roster_players_obj = roster.roster_player.all()
            for player_instance in roster_players_obj:
                serialize = UserSerializer(player_instance.player)
                data = serialize.data
                data['jersey_number'] = player_instance.jersey_number
                data['position'] = player_instance.position
                players.append(data)

            # roster coaches
            roster_coaches_obj = roster.roster_coach.all()
            for coach_instance in roster_coaches_obj:
                serialize = UserSerializer(coach_instance.coach)
                data = serialize.data
                data['jersey_number'] = coach_instance.jersey_number
                data['position'] = coach_instance.position
                coaches.append(data)

        representation['total_players'] = len(players)
        representation['total_coaches'] = len(coaches)
        representation['event_played'] = 0
        representation['total_rosters'] = rosters.count()

        representation['players'] = players
        representation['coaches'] = coaches

        rosters = instance.roster.all()
        events = Event.objects.filter(rosters__in=rosters).distinct()
        event_serialize = EventSerializer(events, many=True)
        representation['event'] = event_serialize.data
        return representation

class PostOrganizationSerializer(serializers.ModelSerializer):
    roster = OrganizationRosterSerializer(read_only=True, many=True, )

    class Meta:
        model = Organization
        fields = ["id", "name", "logo", "sport", "biograph", "roster"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.sport:
            representation["sport"] = SportSerializer(instance.sport).data
        else:
            representation["sport"] = None

        rosters = instance.roster.all()
        players, coaches = [], []
        # roster players
        for roster in rosters:
            roster_players_obj = roster.roster_player.all()
            for player_instance in roster_players_obj:
                serialize = UserSerializer(player_instance.player)
                data = serialize.data
                data['jersey_number'] = player_instance.jersey_number
                data['position'] = player_instance.position
                players.append(data)

            # roster coaches
            roster_coaches_obj = roster.roster_coach.all()
            for coach_instance in roster_coaches_obj:
                serialize = UserSerializer(coach_instance.coach)
                data = serialize.data
                data['jersey_number'] = coach_instance.jersey_number
                data['position'] = coach_instance.position
                coaches.append(data)

        # representation['total_players'] = len(players)
        # representation['total_coaches'] = len(coaches)
        # representation['event_played'] = 0
        # representation['total_rosters'] = rosters.count()

        # representation['players'] = players
        # representation['coaches'] = coaches

        # rosters = instance.roster.all()
        # events = Event.objects.filter(rosters__in=rosters).distinct()
        # event_serialize = EventSerializer(events, many=True)
        # representation['event'] = event_serialize.data
        return representation

class RosterInvitationActionSerializer(serializers.Serializer):
    notification = serializers.PrimaryKeyRelatedField(
        queryset=Notification.objects.all()
    )
    action = serializers.ChoiceField(choices=(
        ("accept", "accept"),
        ("reject", "reject"),
    ))


class RosterGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterGrade
        fields = ("id", "name",)


class AssignJerseyNumberSerializer(serializers.Serializer):
    roster = serializers.PrimaryKeyRelatedField(
        queryset=Roster.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(Q(user_role="player") | Q(user_role="coach"))
    )
    jersey_number = serializers.IntegerField()
    position = serializers.CharField(required=False, default="")

    def validate(self, attrs):
        players = attrs.get("roster").roster_player.all()
        coaches = attrs.get("roster").roster_coach.all()
        user = attrs.get("user")

        if players.filter(player=user).exists() and coaches.filter(coach=user).exists():
            raise serializers.ValidationError({
                "user": "This player/coach does not exits in the roster. "
            })
        return attrs


class RosterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterExitRequest
        fields = ("roster", )



class HandlerRosterExitSerializer(serializers.Serializer):
    notification = serializers.PrimaryKeyRelatedField(
        queryset=Notification.objects.all()
    )
    action = serializers.ChoiceField(choices=(
        ("accept", "accept"),
        ("reject", "reject"),
    ))
