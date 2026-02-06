import os

from django.db.models import Avg
from rest_framework import serializers

from common.models import Feed
from players.models import FeedBadgeRating, Badge, FeedBadges
from .serializers import BadgeSerializer
from .signup import UserSerializer
from players.api.services import post_video_thumbnail


class FeedSkillsRatingSerializer(serializers.ModelSerializer):
    # user = UserSerializer(read_only=True)

    class Meta:
        model = FeedBadgeRating
        fields = ("id", "rating", "rate_badge")
        extra_kwargs = {
            "rate_badge": {"write_only": True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['fullname'] = instance.user.get_full_name()

        return representation


class FeedBadgesSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        ratings = FeedBadgeRating.objects.filter(rate_badge=instance)
        try:
            request = self.context.get("request")
            user_rating = ratings.filter(user=request.user).first()
        except:
            user_rating = None

        result = ratings.aggregate(avg_rating=Avg('rating'))
        average_rating = result['avg_rating']
        average_rating = max(1, min(5, round(average_rating))) if average_rating else 0

        return {
            "id": instance.id,
            "total_rated_user": ratings.count(),
            "average_rating": average_rating,
            "details": BadgeSerializer(instance.badge).data,
            "rating": FeedSkillsRatingSerializer(user_rating).data if user_rating else ""
        }


class FeedPostSerializer(serializers.ModelSerializer):
    badges = serializers.PrimaryKeyRelatedField(
        queryset=Badge.objects.filter(is_admin_assignable=False),
        many=True,
        required=False,
        write_only=True
    )
    user = serializers.SerializerMethodField(read_only=True, method_name="user_details")
    is_like = serializers.SerializerMethodField(read_only=True, method_name="is_user_like")

    class Meta:
        model = Feed
        fields = ("id", "file", "caption", "badges", "tags", "user", "is_like", "thumbnail")
        read_only_fields = ("thumbnail",)

    def validate(self, attrs):
        errors = {}
        try:
            if len(attrs.get("badges")) > 3:
                errors['badges'] = "You can not select up to 3 badges."
        except:
            pass

        file = attrs.get('file')
        if file:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.heic', ]:
                status, data = post_video_thumbnail(file)
                if status is False:
                    errors['file'] = data
                else:
                    attrs['thumbnail'] = data

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        action = self.context.get("action")
        if action == "read":
            self.fields['tags'] = UserSerializer(many=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["badges"] = FeedBadgesSerializer(instance.badges_objects, many=True).data
        try:
            extension = os.path.splitext(instance.file.url)[1]
            video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            if extension in video_exts:
                representation['file_type'] = "video"
            else:
                representation['file_type'] = "image"
        except:
            pass
        return representation

    def user_details(self, obj):
        return UserSerializer(obj.user).data

    def is_user_like(self, obj):
        try:
            request = self.context.get("request")
            if obj.liker.filter(email=request.user.email).exists():
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def update(self, instance, validated_data):
        badges = validated_data.get("badges")
        tags = validated_data.get("tags")
        print("badges", badges)

        if tags is not None:
            validated_data.pop("tags")
            instance.tags.set(tag for tag in tags)

        if badges is not None:
            feed_badges = instance.feed_badge.all()
            new_badges_id = []
            for badge in badges:
                if feed_badges.filter(badge=badge).exists():
                    new_badges_id.append(str(badge.id))
                    badges.remove(badge)
                else:
                    FeedBadges.objects.create(feed=instance, badge=badge)
                    new_badges_id.append(str(badge.id))

            print("new_badges_id ", new_badges_id)
            for badge in instance.feed_badge.all():
                if str(badge.badge.id) not in new_badges_id:
                    badge.delete()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
