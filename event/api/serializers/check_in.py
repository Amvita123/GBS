from rest_framework import serializers
from players.models import Player
from event.models import Event, EventCheckIn, Team
from django.utils import timezone


class EventCheckInSerializer(serializers.Serializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), required=False)
    jersey_number = serializers.IntegerField()
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.filter(is_deleted=False),
        error_messages={
            "does_not_exist": "The specified event does not exist or has been deleted.",
            "incorrect_type": "Invalid event ID. Expected a primary key value."
        }
    )

    def validate(self, attrs):

        event = attrs.get("event")
        if event.end_date:
            if event.end_date.date() < timezone.now().date():
                raise serializers.ValidationError({"event": "This event has already ended, you can't check in."})

        else:
            if event.date.date() < timezone.now().date():
                raise serializers.ValidationError({"event": "This event has already ended, you can't check in."})

        if event.is_active is False:
            raise serializers.ValidationError({"event": "Event is currently inactive you can't checkin."})

        team = attrs.get("team")
        event_teams = event.teams.all()
        if event_teams.filter(id=team.id).exists() is False:
            raise serializers.ValidationError({"team": "This team doesn't exits to this event."})

        return attrs


class EventCheckedInSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        roster_name = instance.roster.name.title() if instance.roster else ""
        team_name = instance.team.name.title() if instance.team else ""
        # if not team_name:
        #     team_name = instance.squad.title()

        user = self.context.get("user")
        verification = user.verification.filter(status="accept").first()
        return {
            "roster": roster_name,
            "team": team_name,
            "jersey_number": instance.jersey_number,
            "verified_pic": verification.photo.url if verification and verification.photo else ""
        }


