from rest_framework import generics, status
from rest_framework.response import Response
from .serializer import *
from players.api.serializers.post import FeedPostSerializer
from common.models import Comment, ReportReasons
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .services import DashboardFeedPagination, send_feed_notification
from common.utils import CustomLimitOffsetPagination
from rest_framework.pagination import PageNumberPagination
from users.models import BlockUser
from chatapp.models import PersonalChat
from notification.task import send_user_action_notification
from rest_framework.permissions import IsAuthenticated, AllowAny
from coach.api.services import IsCoachFanUser
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render


class FeedLike(generics.CreateAPIView):
    serializer_class = FeedLikeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            feed = serializer.validated_data['feed']
            if feed.liker.filter(email=request.user.email).exists():
                feed.liker.remove(request.user)
                feed.like = feed.like - 1
                is_like = False
                action = "dislike"
            else:
                feed.liker.add(request.user)
                feed.like = feed.like + 1
                is_like = True
                action = "like"

            feed.save()
            # serialize = FeedPostSerializer(feed, context={'action': "read"})
            send_feed_notification(request, feed, action)
            return Response({
                "status": "Like action performed.",
                "like": feed.like,
                "is_like": is_like
            })


class FeedComment(generics.GenericAPIView):
    serializer_class = FeedCommentSerializer

    def get(self, request, *args, **kwargs):
        if kwargs.get("feed_pk", None) is None:
            return Response({"status": "invalid feed id"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Comment.objects.select_related("feed").filter(feed_id=kwargs.get("feed_pk")).order_by('-created_at')
        serialize = self.serializer_class(queryset, many=True)
        return Response(serialize.data)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={"request": request})
        if serializer.is_valid(raise_exception=True):
            comment = serializer.save(user=request.user)
            serialize = self.serializer_class(comment)
            send_feed_notification(request, comment.feed, "comment")
            return Response(serialize.data)

    def get_object(self):
        return get_object_or_404(
            Comment.objects.select_related("feed", "user"),
            id=self.kwargs.get("feed_pk"),
            user=self.request.user
        )

    def patch(self, request, *args, **kwargs):
        try:
            queryset = self.get_object()
            serializer = self.serializer_class(queryset, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                comment = serializer.save()
                return Response(self.serializer_class(comment).data)
        except Exception as e:
            return Response(
                {"status": f"{str(e)} id - {kwargs.get('feed_pk')}"},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, *args, **kwargs):
        try:
            queryset = self.get_object()
            queryset.delete()
            return Response({
                "status": "comment has been deleted successfully."
            }, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"status": f"{str(e)} id - {kwargs.get('feed_pk')}"},
                status=status.HTTP_404_NOT_FOUND
            )


class FeedReportView(generics.ListCreateAPIView):
    serializer_class = FeedReportSerializer

    def get(self, request, *args, **kwargs):
        feed_id = self.request.query_params.get("feed_id")
        if feed_id is None:
            return Response({"status": "post id doest not found at query parameter"},
                            status=status.HTTP_400_BAD_REQUEST
                            )
        queryset = FeedReport.objects.filter(feed__id=feed_id)
        serialize = self.serializer_class(queryset, many=True)
        return Response(serialize.data)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            report = serializer.save(user=request.user)
            serialize = self.serializer_class(report)
            send_feed_notification(request, report.feed, "report")
            return Response(
                serialize.data,
                status=status.HTTP_200_OK
            )


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page'
    max_page_size = 100


class FeedReportReason(generics.ListAPIView):
    serializer_class = ReportReasonsSerializer
    queryset = ReportReasons.objects.all()


class DashboardFeed(generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = DashboardFeedSerializer

    def post(self, request, *args, **kwargs):
        serializer = CoachFanFeedSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            feed = serializer.save(user=request.user)
            return Response(DashboardFeedSerializer(feed, context={"request": request}).data)

    def get(self, request, *args, **kwargs):
        post_id = self.request.query_params.get("id", None)
        user_id = self.request.query_params.get("user_id", None)
        organization_id = self.request.query_params.get("organization_id", None)
        roster_id = self.request.query_params.get("roster_id", None)

        blocked_relations = BlockUser.objects.filter(Q(blocked=request.user) | Q(blocker=request.user))
        blocker_ids = list(set(
            list(
                blocked_relations.values_list('blocked_id', flat=True)
            ) + list(
                blocked_relations.values_list('blocker_id', flat=True)
            )
        ))

        try:
            blocker_ids.remove(request.user.id)
        except:
            pass

        if user_id:
            queryset = Feed.objects.filter(user__id=user_id).exclude(user_id__in=blocker_ids).select_related('roster')
        elif organization_id:
            queryset = Feed.objects.filter(roster__organization__id=organization_id).exclude(
                user_id__in=blocker_ids).select_related('roster')
        elif roster_id:
            queryset = Feed.objects.filter(roster__id=roster_id).exclude(user_id__in=blocker_ids).select_related(
                'roster')
        else:
            queryset = Feed.objects.all().exclude(user_id__in=blocker_ids).select_related('roster')
        if post_id:
            queryset = queryset.filter(id=post_id).first()
            serialize = self.serializer_class(queryset, context={"request": request, "liker": True})
            return Response(serialize.data)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        serialize = self.serializer_class(result_page, many=True, context={"request": request})
        return paginator.get_paginated_response(serialize.data)

    def patch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": "pk is required"
            })
        post = get_object_or_404(Feed, id=pk, user=request.user)
        serializer = FeedUpdateSerializer(instance=post, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_200_OK, data={"detail": "Post has been updated successfully."})

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsCoachFanUser()]

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": "pk is required"
            })
        post = get_object_or_404(Feed, id=pk, user=request.user)
        post.delete()
        return Response(status=status.HTTP_200_OK, data={
            "detail": "Post has been deleted successfully."
        })


class FeedShare(APIView):

    def post(self, request, *args, **kwargs):
        serializer = FeedShareSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = []
            for i in serializer.validated_data['users']:
                # add message to chat
                data.append(PersonalChat(
                    sender=request.user,
                    message=serializer.validated_data.get("message", ""),
                    receiver=i,
                    post=serializer.validated_data['post']
                ))
                # post share notification
                if i.username != request.user.username:
                    send_user_action_notification.delay(
                        title="Post share",
                        action="post_detail",
                        sender=request.user.username,
                        receiver=i.username,
                        object_id=serializer.validated_data['post'].id,
                        message=f"{request.user.username.title()} has share a post. check your conversation."
                    )

            PersonalChat.objects.bulk_create(data)
            return Response({"detail": "post has been shared successfully."})


class MyFeed(generics.ListAPIView):
    serializer_class = DashboardFeedSerializer

    # pagination_class = StandardResultsSetPagination()

    def get_queryset(self):
        return Feed.objects.filter(user=self.request.user)


# class AndroidDeeplink(APIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request, *args, **kwargs):
#         return Response(
#             [
#                 {
#                     "relation": ["delegate_permission/common.handle_all_urls"],
#                     "target": {
#                         "namespace": "android_app",
#                         "package_name": "com.athleterated.athlete_rated",
#                         "sha256_cert_fingerprints": [
#                             "78:FA:FF:93:1C:02:66:F7:76:FB:52:A8:DC:AF:1B:EA:DF:D2:F7:3C:6A:41:5A:E8:53:BD:FE:89:45:B0:17:4F"
#                         ]
#                     }
#                 }
#             ]
#         )


def AndroidDeeplink(request):
    data = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.athleterated.athlete_rated",
                "sha256_cert_fingerprints": [
                    "78:FA:FF:93:1C:02:66:F7:76:FB:52:A8:DC:AF:1B:EA:DF:D2:F7:3C:6A:41:5A:E8:53:BD:FE:89:45:B0:17:4F",
                    "C3:85:6D:05:A3:DE:90:8B:53:6A:48:0D:C3:6C:C9:C6:C9:35:3A:76:3A:E9:79:DE:C4:F3:AF:B9:4A:ED:65:5B",
                    "0A:37:C7:68:30:D4:53:6A:8D:27:73:70:77:D8:9A:9C:83:80:3C:EE:82:15:DF:F2:E8:02:38:93:F4:8A:9C:28"
                ]
            }
        }
    ]

    return JsonResponse(data, safe=False)


def IosDeeplink(request):
    data = {
        "applinks": {
            "apps": [],
            "details": [
                {
                    "appID": "XG39NJQ86A.com.tech.athleterated",
                    "paths": ["/app/*"]
                }
            ]
        }
    }
    return JsonResponse(
        data, safe=False
    )
