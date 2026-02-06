from rest_framework import serializers

from coach.api.serializer import RosterListSerializer
from coach.models import Roster
from event.models import Event, EventRules, EventPlan, Team, EventCheckIn
from datetime import date, datetime, timedelta
from .follow import EventFollowUser
from event.api.serializers.check_in import EventCheckedInSerializer
from django.utils import timezone


class EventRuleSerializer(serializers.ModelSerializer):
    # event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    class Meta:
        model = EventRules
        fields = ['id', 'text', ]


class EventSerializer(serializers.ModelSerializer):
    event_follower = EventFollowUser(many=True, read_only=True)
    rules = EventRuleSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    is_follow = serializers.SerializerMethodField(read_only=True)
    rule = serializers.ListField(write_only=True, required=False)
    plan = serializers.PrimaryKeyRelatedField(write_only=True, required=False,
                                              queryset=EventPlan.objects.filter(is_active=True, is_deleted=False))
    location = serializers.CharField(required=True)
    event_type = serializers.ChoiceField(choices=Event.EVENT_TYPE_CHOICES, required=True)
    rosters = RosterListSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'name', "logo", 'is_follow', 'date', 'status', 'description', "location", "event_type", 'rules',
                  'booking_link',
                  "event_follower", "rule", "plan", "location", "is_active", "rosters", "end_date"]

    # def get_status(self, obj):
    #     if obj.date < datetime.now():
    #         return "completed"
    #     else:
    #         return "upcoming"

    def get_status(self, obj):
        now = timezone.now()

        if obj.end_date:
            if now < obj.date:
                # Event hasn't started yet
                time_until_start = obj.date - now
                if time_until_start <= timedelta(hours=2):
                    return "starting_soon"
                else:
                    return "upcoming"

            elif now > obj.end_date:
                # Event has completely ended
                return "completed"

            else:
                # Event is currently happening (between start and end date)
                time_since_start = now - obj.date
                time_until_end = obj.end_date - now

                # Just started (within first 30 minutes)
                if time_since_start <= timedelta(minutes=30):
                    return "live"

                # About to end (within last hour)
                elif time_until_end <= timedelta(hours=1):
                    return "ending_soon"

                # In the middle of the event
                else:
                    return "ongoing"

        # Single-point events (no end_date)
        else:
            if obj.date > now:
                time_until = obj.date - now
                if time_until <= timedelta(hours=2):
                    return "starting_soon"
                else:
                    return "upcoming"
            else:
                time_since = now - obj.date
                if time_since <= timedelta(minutes=30):
                    return "live"
                else:
                    return "completed"

    def get_is_follow(self, instance):
        try:
            user = self.context.get("request").user
            follower = instance.event_follower.all()
            if follower.filter(user=user).exists():
                return True
            return False
        except:
            return False

    def create(self, validated_data):
        rules = validated_data.pop('rule', [])
        event = Event.objects.create(**validated_data)
        for rule in rules:
            EventRules.objects.create(event=event, text=rule)

        return event

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = instance.name.title()
        representation['location'] = instance.location.title()
        user = self.context.get("request").user

        is_ended = False
        if instance.end_date:
            is_ended = instance.end_date < timezone.now()
        else:
            is_ended = instance.date < timezone.now()

        try:
            user_id = self.context.get("request").user.id
            if str(user_id) == str(instance.user.id):
                representation['is_owner'] = True
            else:
                representation['is_owner'] = False
        except Exception as e:
            print(e)
            representation['is_owner'] = False
        representation['is_ended'] = is_ended

        # check_in_obj = EventCheckIn.objects.filter(user=user, event=instance)
        representation['is_check'] = EventCheckIn.objects.filter(user=user, event=instance).exists()
        # representation['check_in'] = {}
        # if check_in_obj.exists():
        #     representation["check_in"] = EventCheckedInSerializer(check_in_obj.first(), context={"user": user}).data

        return representation

    def validate_booking_link(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Booking link must be a JSON dictionary object.")

        if not value:
            raise serializers.ValidationError("Booking link can't be empty.")

        for k, v in value.items():
            if not isinstance(v, str):  # or not v.startswith(("http://", "https://"))
                raise serializers.ValidationError(f"Invalid URL for key '{k}': {v}")

        return value

    def update(self, instance, validated_data):
        logo = validated_data.pop('logo', None)
        rules = validated_data.pop('rule', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if logo:
            instance.logo = logo
        instance.save()

        if rules:
            instance.rules.all().delete()
            rules_obj = [EventRules(event=instance, text=rule) for rule in rules]
            EventRules.objects.bulk_create(rules_obj, ignore_conflicts=True)

        return instance


class EventTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name"]


class EventLeaderBoardSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        rank_map = self.context.get("rank_map", {})
        team_names = self.context.get("team_names", {})

        return {
            "id": instance.id,
            "first_name": instance.first_name.title(),
            "last_name": instance.last_name.title(),
            "profile_pic": instance.profile_pic.url if instance.profile_pic else "",
            "overall_rating": instance.overall_rating,
            "badge_count": instance.badge_count,
            "template_count": instance.template_count,
            "rank": rank_map.get(instance.id),
            "team": team_names.get(instance.id),
        }


class RosterSubmitSerializer(serializers.Serializer):
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.filter(is_active=True),
    )
    rosters = serializers.PrimaryKeyRelatedField(
        queryset=Roster.objects.filter(is_active=True),
        many=True
    )
