from rest_framework import serializers
from common.models import ProjectSettings, AppRelease



class ProjectSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSettings
        fields = [
            'player_verification',
            'coach_verification',
            'organization_create',
            'admin_subscription',
        ]


class AppReleaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = AppRelease
        fields = [
            'app_version',
            'build_number',
            'min_supported_build',
            'force_update',
            'release_notes',
        ]

