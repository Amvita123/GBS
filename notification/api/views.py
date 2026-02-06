from notification.models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, generics
from .serializer import NotificationSerializer, NotificationSendSerializer
from notification.task import send_user_action_notification


class NotificationView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.select_related("to_user").filter(
            to_user=self.request.user, is_active=True).order_by('-created_at')

    def post(self, request, *args, **kwargs):
        serializer = NotificationSendSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            send_user_action_notification.delay(
                sender=request.user.username,
                receiver=serializer.validated_data['to'].username,
                message=serializer.validated_data.get("message"),
                action=serializer.validated_data['action'],
                object_id=serializer.validated_data.get("object_id")
            )
            return Response({
                "status": "notification has been sent"
            })
