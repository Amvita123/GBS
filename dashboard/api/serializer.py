from rest_framework import serializers

from coach.models import Roster
from common.models import Feed, Comment, FeedReport, ReportReasons
from users.serializers import UserSerializer
from players.api.serializers.post import FeedPostSerializer, FeedBadgesSerializer
from urllib.parse import urlparse
from common.services import human_readable_timesince
from users.models import User
from players.api.services import post_video_thumbnail
from coach.api.serializer import OrganizationListSerializer, OrganizationRosterSerializer, PostOrganizationSerializer
import os


class FeedLikeSerializer(serializers.Serializer):
    feed_id = serializers.UUIDField()

    def validate(self, attrs):
        feed = Feed.objects.filter(id=attrs.get("feed_id"))
        if feed.exists():
            attrs['feed'] = feed.first()
            return attrs
        raise serializers.ValidationError({"feed_id": "invalid feed id not found."})


class FeedCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "text", "created_at", "user", "feed",)
        extra_kwargs = {
            'feed': {'write_only': True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['created_at'] = human_readable_timesince(instance.created_at)
        return representation


class ReportReasonsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportReasons
        fields = ("id", "reason")


class FeedReportSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = FeedReport
        fields = ("id", "reason", "feed", "other_reason", "user")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        reason = ReportReasonsSerializer(instance.reason)
        representation['reason'] = reason.data
        return representation

    def validate(self, attrs):
        if attrs.get("other_reason") is not None:
            if attrs.get("reason").reason.lower() != "other":
                raise serializers.ValidationError({"other_reason": "please select other reason."})

        return attrs

class DashboardFeedSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    badges = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField(method_name="post_comments")
    is_like = serializers.SerializerMethodField(read_only=True, method_name="is_user_like")
    organization = serializers.SerializerMethodField()

    class Meta:
        model = Feed
        fields = (
            "id", "file", 'thumbnail', "caption", "link", "like", "is_like", "created_at", "user", "badges", "tags", "comments", "organization")

    def get_badges(self, obj):
        request = self.context.get("request")
        badges = FeedBadgesSerializer(obj.badges_objects, many=True, context={"request": request}).data
        return badges

    def post_comments(self, obj):
        return FeedCommentSerializer(
            obj.comments.all(),
            many=True
        ).data

    def is_user_like(self, obj):
        request = self.context.get("request")
        if obj.liker.filter(email=request.user.email).exists():
            return True
        return False

    def get_organization(self, obj):
        if obj.roster and obj.roster.organization:
            return PostOrganizationSerializer(obj.roster.organization).data
        return ""

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.file:
            parsed_url = urlparse(instance.file.url)
            representation['file'] = parsed_url.path
        representation['created_at'] = human_readable_timesince(instance.created_at)
        representation['tags'] = UserSerializer(instance.tags.all(), many=True).data
        try:
            extension = os.path.splitext(instance.file.url)[1]
            video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            if extension in video_exts:
                representation['file_type'] = "video"
            else:
                representation['file_type'] = "image"
        except:
            pass

        # likes users
        if self.context.get("liker", None):
            representation['like_users'] = UserSerializer(instance.liker.all(), many=True).data

        return representation

class CoachFanFeedSerializer(serializers.ModelSerializer):
    roster = serializers.PrimaryKeyRelatedField(
        queryset=Roster.objects.all(),
        error_messages={
            'does_not_exist': 'The roster with this ID does not exist.'
        }
    )

    class Meta:
        model = Feed
        fields = ("id", "file", "caption", "tags", "roster")

    def validate_roster(self, value):
        request = self.context.get("request")
        if request and value.organization.created_by != request.user:
            raise serializers.ValidationError(
                "You can only create posts for your own rosters."
            )
        return value

    def create(self, validated_data):
        tags = validated_data.pop("tags") if validated_data.get("tags") is not None else []
        feed = Feed.objects.create(
            **validated_data
        )
        feed.tags.set(tag for tag in tags)

        return feed

    def validate(self, attrs):
        file = attrs.get('file')

        if file:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.heic', ]:
                status, data = post_video_thumbnail(file)
                if status is False:
                    raise serializers.ValidationError({'file': data})
                else:
                    attrs['thumbnail'] = data

        return attrs


class FeedShareSerializer(serializers.Serializer):
    post = serializers.PrimaryKeyRelatedField(
        queryset=Feed.objects.all()
    )
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        many=True
    )
    message = serializers.CharField(required=False)


class FeedUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ("file", "caption", "link", "tags", "organization", "roster")
