from rest_framework import serializers
from players.models import Player, Sport, Position, PlayingStyle, Badge, Squad, Challenge, BadgeLevel, \
    BadgeLevelTemplate
from common.models import Skill
from django.db.models import Q
from django.db.models import Case, When, Value, IntegerField


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ("id", "name", "description", "level", "file_url")


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ("id", "name")


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ("id", "name")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = instance.name.title()
        return representation


class PlayingStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayingStyle
        fields = ("id", "title")


class PlayerBadgeSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        if instance.badge_level:
            badge_level_icon = instance.badge_level.icon.url
        else:
            if instance.badge.icon:
                badge_level_icon = instance.badge.icon.url
            else:
                badge_level_icon = ""
        if instance.badge_level:
            earned_template = [" ".join(i.split()).lower().replace(' ', '') for i in instance.templates]
            templates = [
                {"title": i.title, "is_earned": True if i.title.lower().replace(' ', '') in earned_template else False}
                for i in
                instance.badge_level.badge_template.all()
            ]

        else:
            templates = []

        return {
            "name": instance.badge.name,
            "level": instance.badge_level.name if instance.badge_level else "",
            'icon': badge_level_icon,
            "point": instance.point,
            "templates": templates,
        }


class ProfileSerializer(serializers.ModelSerializer):
    position = PositionSerializer()

    # squad = serializers.SerializerMethodField(read_only=True)
    #
    # def get_squad(self, obj):
    #     from players.api.serializers.squad import SquadSerializer
    #     user_squad = Squad.objects.select_related("created_by").filter(created_by=obj.user).first()
    #     if user_squad:
    #         return SquadSerializer(user_squad).data
    #     return None

    class Meta:
        model = Player
        fields = ("id", 'weight', "height", "overall_rating", "sport", "position", "grade", )

        extra_kwargs = {
            "overall_rating": {"read_only": True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['squad_count'] = Squad.objects.select_related("created_by").prefetch_related("players").filter(
            Q(created_by=instance.user) |
            Q(players=instance.user)
        ).distinct().count()

        try:
            user_squad = instance.user.owner
            challenges = Challenge.objects.filter(
                Q(first_squad=user_squad) |
                Q(second_squad=user_squad),
                is_accepted=True,
                winner__isnull=False,
                point_first_squad__isnull=False,
                point_second_squad__isnull=False
            )
            win = challenges.filter(winner=user_squad).count()
            representation['win'] = win
            representation['loss'] = challenges.count() - win

        except:
            representation['win'] = 0
            representation['loss'] = 0

        representation['sport'] = instance.sport.name
        if instance.position:
            representation['position']['playing_style'] = instance.playing_style.title

        representation['weight'] = instance.weight if instance.weight is not None else 0
        representation['height'] = instance.height if instance.height is not None else 0
        representation['badge'] = PlayerBadgeSerializer(instance.user.badge.all(), many=True).data
        representation["overall_rating"] = float(representation["overall_rating"])
        user_squad = Squad.objects.select_related("created_by").filter(created_by=instance.user).first()
        representation['squad_id'] = user_squad.squad_id if user_squad else ""
        return representation


class BadgeTemplateCheckList(serializers.ModelSerializer):
    class Meta:
        model = BadgeLevelTemplate
        fields = ['id', 'title']


class BadgeLevelSerializer(serializers.ModelSerializer):
    badge_template = BadgeTemplateCheckList(many=True, read_only=True)

    class Meta:
        model = BadgeLevel
        fields = ('id', "name", 'icon', 'badge_template',)


class BadgeSerializer(serializers.ModelSerializer):
    # badge_level = BadgeLevelSerializer(many=True, read_only=True)
    badge_level = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ("id", "name", "description", 'icon', "badge_level",)

    def get_badge_level(self, obj):
        badge_levels = obj.badge_level.annotate(
            custom_order=Case(
                When(name="bronze", then=Value(0)),
                When(name="silver", then=Value(1)),
                When(name="gold", then=Value(2)),
                default=Value(99),
                output_field=IntegerField(),
            )
        ).order_by("custom_order")

        return BadgeLevelSerializer(badge_levels, many=True).data
