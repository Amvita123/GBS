from common.models import Setting, ProjectSettings,AppRelease
from .serializers.termsconditions import TermsConditionSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers.project_settings import AppReleaseSerializer, ProjectSettingsSerializer


class TermsConditionAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        obj = Setting.objects.first()
        if obj:
            serializer = TermsConditionSerializer(obj)
            return Response(serializer.data)
        return Response({"message": "terms & privacy policy not added"}, status=status.HTTP_404_NOT_FOUND)


class ProjectSettingsAPIView(APIView):
    permission_classes = [AllowAny]


    def get(self, request):
        project_conf = ProjectSettings.objects.first()
        app_release_ios = AppRelease.objects.filter(platform="IOS").order_by("-created_at").first()
        app_release_android = AppRelease.objects.filter(platform="ANDROID").order_by("-created_at").first()

        project_conf_serialize = ProjectSettingsSerializer(project_conf).data
        serialize_ios_release = AppReleaseSerializer(app_release_ios).data
        serialize_android_release = AppReleaseSerializer(app_release_android).data

        return Response(
            {
                "detail": "settings fetch successfully",
                "app_release": {
                    "android":serialize_android_release,
                    "ios":serialize_ios_release,
                },
                "payment": project_conf_serialize,
            }
        )