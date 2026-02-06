from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from players.api.services import IsPlayerUser
from players.models import Squad, Challenge
from django.db.models import Q
from datetime import datetime, timedelta
from common.services import smart_timesince

from .serializers import ChallengeGroupSerializer, ChallengeChatSerializer

from chatapp.models import ChallengeGroupChat, PersonalChat


class PlayerChallengeGroup(APIView):
    permission_classes = [IsPlayerUser]

    def get(self, request):
        user_squad = Squad.objects.select_related("created_by").prefetch_related("players").filter(
            Q(created_by=request.user) |
            Q(players=request.user)
        )
        user_squad_list = [squad.id for squad in user_squad]
        challenges = Challenge.objects.select_related("first_squad", "second_squad").filter(
            Q(first_squad__id__in=user_squad_list) |
            Q(second_squad__id__in=user_squad_list),
            is_accepted=True,
            result_date__gt=datetime.now().date() - timedelta(days=1)
        )
        group = ChallengeGroupSerializer(challenges, many=True)

        return Response(group.data)


class ChallengeChatView(APIView):
    permission_classes = [IsPlayerUser]

    def get(self, request, challenge_id):
        queryset = ChallengeGroupChat.objects.select_related("challenge", "users").filter(
            Q(
                Q(challenge__first_squad__players=request.user) |
                Q(challenge__second_squad__players=request.user),
            ),
            challenge__challenge_id=challenge_id
        ).distinct()

        serialize = ChallengeChatSerializer(queryset, many=True)

        return Response(serialize.data)


class UserConnectionsView(APIView):

    def get(self, request, *args, **kwargs):
        chats = PersonalChat.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        query = self.request.query_params.get("q")

        connections = {}

        for chat in chats.order_by("-created_at"):
            other_user = chat.receiver if chat.sender == request.user else chat.sender
            if other_user.id not in connections:  # only pick latest message
                connections[other_user.id] = {
                    "user": other_user,
                    "last_message": chat.message,
                    "last_message_at": chat.created_at,
                }

        result = []
        for conn in connections.values():
            data = {
                "id": conn["user"].id,
                "email": conn["user"].email,
                "first_name": conn["user"].first_name,
                "last_name": conn["user"].last_name,
                "username": conn["user"].username,
                "is_username_enable": conn["user"].is_username_enable,
                "last_message": conn["last_message"],
                "last_message_at": smart_timesince(conn["last_message_at"]),
                "profile_pic": conn["user"].profile_pic.url if conn["user"].profile_pic else ""

            }
            if query:
                keys = f'{conn["user"].email} {conn["user"].first_name} {conn["user"].last_name} {conn["user"].username}'.lower()
                if query.lower() in keys:
                    result.append(data)
            else:
                result.append(data)

        return Response(result)
