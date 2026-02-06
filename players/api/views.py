from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import IntegrityError

from common.models import Feed, Skill
from players.models import (
    Player, Squad, FeedBadges, FeedBadgeRating, Badge,
    Challenge, Position, SquadStructure, Sport, PlayingStyle,
    SchoolGrade
)
from common.utils import CustomLimitOffsetPagination
from .serializers import *
from .serializers.post import FeedPostSerializer, FeedSkillsRatingSerializer
from .serializers.squad import SquadSerializer, SquadStructureSerializer, SquadLeaderboardSerializer
from .serializers.challenge import ChallengeSerializer, ChallengeActionSerializer
from .services import IsPlayerUser, PostFilter, SkillFilter

from players.task import player_badge_assign

from notification.task import send_challenge_request_notification, disable_notification_action

from datetime import datetime
from rest_framework.permissions import AllowAny, IsAuthenticated
from players.api.utils import validate_squad_structure
from django.db.models import Min
from django.db.models import F, FloatField, Case, When, Value
from django.db.models.functions import Cast
from django.db.models import ExpressionWrapper
from coach.models import Roster, RosterExitRequest, RosterPlayer
from coach.api.serializer import RosterSerializer, RosterRequestSerializer
from notification.task import send_single_user_admin_notification


class Profile(APIView):
    serializer_class = ProfileSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                player = Player.objects.create(
                    user=request.user,
                    **serializer.validated_data
                )
            except Exception as e:
                return Response({"error": str(e)})
            serialize = self.serializer_class(player)
            return Response({
                "status": "player profile created successfully",
                "data": serialize.data
            }, status=status.HTTP_200_OK)


class Post_Feed(APIView):
    permission_classes = [IsPlayerUser]
    pagination_class = CustomLimitOffsetPagination()

    def post(self, request):
        serializer = FeedPostSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            badges = serializer.validated_data.pop("badges") if "badges" in dict(serializer.validated_data) else []
            tags = serializer.validated_data.pop("tags") if serializer.validated_data.get("tags") is not None else []

            feed = Feed.objects.create(
                user=request.user,
                **serializer.validated_data
            )

            feed.tags.set(tag for tag in tags)

            FeedBadges.objects.bulk_create(
                [
                    FeedBadges(feed=feed, badge=badge) for badge in badges
                ]
            )

            serialize = FeedPostSerializer(feed, context={'action': "read"})
            return Response(
                serialize.data,
                status=status.HTTP_200_OK
            )

    def get(self, request):
        post_id = self.request.query_params.get("id", None)
        queryset = Feed.objects.select_related("user").filter(user=request.user).order_by("-created_at")
        if post_id:
            queryset = queryset.filter(id=post_id)
            serialize = FeedPostSerializer(queryset.first(), context={
                'action': "read"
            })
            return Response(serialize.data)
        result_page = self.pagination_class.paginate_queryset(queryset, request)

        serialize = FeedPostSerializer(result_page, many=True, context={
            'action': "read"
        })
        return self.pagination_class.get_paginated_response(serialize.data)

    def patch(self, request, feed_id):
        queryset = Feed.objects.select_related("user").filter(user=request.user, id=feed_id)
        if queryset.exists() is False:
            return Response(
                {"status": "Invalid post id"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = FeedPostSerializer(queryset.first(), data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            post = serializer.save()
            serialize = FeedPostSerializer(post, context={'action': "read"})
            return Response(serialize.data)

    def delete(self, request, feed_id):
        queryset = Feed.objects.select_related("user").filter(user=request.user, id=feed_id)
        if queryset.first():
            queryset.first().delete()
            return Response({"status": "post deleted successfully"},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({"status": "Invalid post id not found"},
                        status=status.HTTP_404_NOT_FOUND
                        )


class SquadView(generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = SquadSerializer
    permission_classes = [IsPlayerUser]

    def get_queryset(self):
        q = self.request.query_params.get("q", self.kwargs.get("pk"))
        if q is not None:
            return Squad.objects.filter(
                Q(name__icontains=q) |
                Q(squad_id__icontains=q) |
                Q(id=q)
            )
        return Squad.objects.select_related("created_by").prefetch_related("players").filter(
            created_by=self.request.user
            # Q(players=self.request.user)
        ).distinct()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # structure validate
            try:
                serializer.validated_data.pop('create_new')
            except:
                pass

            structure_status, players = validate_squad_structure(
                structure=serializer.validated_data['structure'],
                players=serializer.validated_data['players'],
                user=request.user
            )
            if structure_status is False:
                return Response({"players": players}, status=status.HTTP_400_BAD_REQUEST)

            # create squad after valid data
            if Squad.objects.select_related("created_by").filter(
                    created_by=request.user
            ).exists():
                return Response(
                    {"status": "A squad has already been created by you."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            squad = serializer.save(created_by=request.user, players=players)
            # squad.players.add(request.user)
            serialize = self.serializer_class(squad)
            return Response(
                serialize.data,
                status=status.HTTP_200_OK
            )

    def patch(self, request, *args, **kwargs):
        squad = Squad.objects.select_related("created_by").filter(created_by=request.user)
        # squad_id = self.request.query_params.get("id")
        if squad.exists() is False:
            return Response({"status": "You haven't created squad yet."}, status.HTTP_404_NOT_FOUND)

        # if squad_id:
        #     try:
        #         squad = squad.get(id=squad_id)
        #     except Exception as e:
        #         print(e)
        #         return Response({"status": "Squad update failed due to invalid id."}, status.HTTP_404_NOT_FOUND)
        # else:
        squad = squad.first()

        serializer = self.serializer_class(squad, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.validated_data.pop('create_new')
            except:
                pass
            if "players" in serializer.validated_data:
                structure_status, players = validate_squad_structure(
                    structure=serializer.validated_data.get("structure", squad.structure),
                    players=serializer.validated_data.get('players', []),
                    user=request.user
                )

                if structure_status is False:
                    return Response({"players": players}, status=status.HTTP_400_BAD_REQUEST)

            squad = serializer.save(created_by=request.user)
            if squad is False:
                return Response({
                    "details": "squad has been deleted because no user exists."
                })
            serialize = self.serializer_class(squad)
            return Response(
                serialize.data
            )

    def delete(self, request, *args, **kwargs):
        try:
            squad = Squad.objects.select_related("created_by").get(created_by=request.user)
            squad.delete()
            return Response({"status": "Squad has been deleted."},
                            status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(e)
            return Response({"status": "You haven't created squad yet."}, status.HTTP_404_NOT_FOUND)

    # def get_serializer_context(self):
    #     context = super().get_serializer_context()
    #     context.update({
    #         "request": self.request
    #     })
    #     return context

    def put(self, request, *args, **kwargs):
        squad = Squad.objects.select_related("created_by").filter(created_by=request.user)
        if squad.exists() is False:
            return Response({"status": "You haven't created squad yet."}, status.HTTP_404_NOT_FOUND)
        
        squad = squad.first()
        serializer = self.serializer_class(squad, data=request.data)
        if serializer.is_valid(raise_exception=True):
            structure_status, players = validate_squad_structure(
                structure=serializer.validated_data.get("structure", squad.structure),
                players=serializer.validated_data.get('players', []),
                user=request.user
            )

            if structure_status is False:
                return Response({"players": players}, status=status.HTTP_400_BAD_REQUEST)

            if serializer.validated_data.get('create_new') is True:
                try:
                    squad.delete()
                except:
                    pass
                serializer = self.serializer_class(None, data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.validated_data.pop('create_new')
                    serializer.save(created_by=request.user, players=players)
            else:
                serializer.save(created_by=request.user, players=players)
            return Response(serializer.data)


class FeedSkillsRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FeedSkillsRatingSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            rating = FeedBadgeRating.objects.select_related("user", "rate_badge").filter(
                user=request.user, rate_badge=serializer.validated_data['rate_badge']
            )
            if rating.exists():
                pre_rating = rating.first()
                pre_rating.rating = serializer.validated_data['rating']
                pre_rating.save()
            else:
                serializer.save(user=request.user)
            player_badge_assign.delay(rate_badge_id=serializer.validated_data['rate_badge'].id)
            return Response({"status": "Successfully rated!"})


class BadgeList(generics.ListAPIView):
    permission_classes = [IsPlayerUser]
    serializer_class = BadgeSerializer
    queryset = Badge.objects.annotate(
        badge_level_name=Min('badge_level__name')
    ).order_by('badge_level_name')
    filterset_class = PostFilter
    # pagination_class = None


class SkillList(generics.ListAPIView):
    permission_classes = [IsPlayerUser]
    serializer_class = SkillSerializer
    queryset = Skill.objects.all()
    filterset_class = SkillFilter


class ChallengeView(APIView):
    serializer_class = ChallengeSerializer
    permission_classes = [IsPlayerUser]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_squad = Squad.objects.select_related("created_by").filter(created_by=request.user)
            if user_squad.exists() is False:
                return Response({
                    "status": "you don't have create squad. create squad to challenge"
                }, status=status.HTTP_404_NOT_FOUND)

            user_squad = user_squad.first()
            if serializer.validated_data['squad'].id == user_squad.id:
                return Response(
                    {"status": "you can't challenge your self."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                challenge = Challenge.objects.create(
                    first_squad=user_squad,
                    second_squad=serializer.validated_data['squad'],
                    result_date=serializer.validated_data['result_date']
                )
                send_challenge_request_notification.delay(
                    sender=request.user.username,
                    receiver=serializer.validated_data['squad'].created_by.username,
                    challenge=challenge.id,
                    message=f"You have been challenged by {request.user.username.title()} on {challenge.result_date.strftime('%m/%d/%Y')}.",
                    is_action=True
                )
            except IntegrityError:
                return Response(
                    {"status": "you have already challenged."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serialize = self.serializer_class(challenge)
            return Response({
                "status": "Challenge request successfully",
                "data": serialize.data
            }, status=status.HTTP_200_OK)

    def get(self, request):
        challenge_id = request.query_params.get("q")
        user_squad = Squad.objects.select_related("created_by").prefetch_related("players").filter(
            Q(created_by=request.user) |
            Q(players=request.user)
        )
        if user_squad.exists() is False:
            return Response({
                "status": "you don't have squad."
            }, status=status.HTTP_404_NOT_FOUND)

        user_squad_list = [squad.id for squad in user_squad]
        challenges = Challenge.objects.filter(
            Q(first_squad__id__in=user_squad_list) |
            Q(second_squad__id__in=user_squad_list),
            is_accepted=True
        )

        if challenge_id:
            try:
                challenge = challenges.get(challenge_id=challenge_id)
                serialize = self.serializer_class(challenge)
                return Response(serialize.data)
            except Exception as e:
                return Response({"status": f"{str(e)}"},
                                status=status.HTTP_404_NOT_FOUND)

        upcoming = challenges.filter(result_date__gt=datetime.now().date())
        past = challenges.filter(result_date__lt=datetime.now().date())
        today = challenges.filter(result_date=datetime.now().date())

        upcoming_serialize = self.serializer_class(upcoming, many=True)
        past_serialize = self.serializer_class(past, many=True)
        today_serialize = self.serializer_class(today, many=True)

        return Response({
            "status": "Ok",
            "today": today_serialize.data,
            "upcoming": upcoming_serialize.data,
            "past": past_serialize.data
        })


class ChallengeAction(APIView):
    permission_classes = [IsPlayerUser]

    def post(self, request):
        serializer = ChallengeActionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_challenge = Challenge.objects.select_related("first_squad", "second_squad").filter(
                second_squad__created_by=request.user,
                challenge_id=serializer.validated_data['challenge_id']
            )
            if user_challenge.exists() is False:
                return Response({"status": "challenge doesn't found."},
                                status=status.HTTP_404_NOT_FOUND)

            if user_challenge.first().is_accepted is not None:
                return Response(
                    {"status": "action has already performed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            action = serializer.validated_data['action']
            user_challenge = user_challenge.first()

            if action == "accept":
                user_challenge.is_accepted = True
                is_click_action = True
            else:
                user_challenge.is_accepted = False
                is_click_action = False

            user_challenge.save()
            disable_notification_action.delay(challenge_id=user_challenge.id)
            send_challenge_request_notification.delay(
                sender=request.user.username,
                receiver=user_challenge.first_squad.created_by.username,
                challenge=user_challenge.id,
                message=f"{request.user.username.title()} has {action}ed the challenge on {user_challenge.result_date.strftime('%m/%d/%Y')}.",
                action=is_click_action
            )

            return Response({"status": "action has performed successfully."})


class Positions(generics.ListAPIView):
    serializer_class = PositionSerializer
    queryset = Position.objects.all()
    permission_classes = [AllowAny]


class PositionPlayingStyle(generics.ListAPIView):
    serializer_class = PlayingStyleSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        queryset = PlayingStyle.objects.select_related("position").filter(position__id=kwargs['pk'])
        serialize = self.serializer_class(queryset, many=True)
        return Response(serialize.data)


class SquadStructureView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SquadStructureSerializer
    queryset = SquadStructure.objects.all()


class AllSports(generics.ListAPIView):
    serializer_class = SportSerializer
    queryset = Sport.objects.all().order_by('name')
    permission_classes = [AllowAny]


class SquadLeaderboard(APIView):

    def get(self, request, *args, **kwargs):
        search = request.GET.get("search", "").strip()

        # build base queryset with annotations
        squads = Squad.objects.annotate(
            total_games=F("win") + F("loss"),
        ).annotate(
            win_percentage=Case(
                When(total_games=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    Cast(F("win"), FloatField()) / Cast(F("win") + F("loss"), FloatField()) * 100,
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        ).order_by(
            F("win_percentage").desc(nulls_last=True),
            F("win").desc()
        )

        # assign global ranks once
        ranked_squads = []
        for idx, squad in enumerate(squads, start=1):
            squad.rank = idx
            squad.players_count = squad.players.count()
            ranked_squads.append(squad)

        # apply search on the ranked list (not on the queryset again)
        if search:
            ranked_squads = [s for s in ranked_squads if search.lower() in s.name.lower()]

        serializer = SquadLeaderboardSerializer(ranked_squads, many=True)

        # current user squad position
        user_squad_rank = None
        try:
            user_squad = Squad.objects.get(created_by=request.user)
            for squad in ranked_squads:  # already has rank
                if squad.id == user_squad.id:
                    user_squad_rank = squad.rank
                    break
        except Squad.DoesNotExist:
            user_squad_rank = None

        response = {
            "detail": "Squad leaderboard loaded successfully",
            "user_squad_rank": user_squad_rank,
            "leaderboard": serializer.data,
        }
        return Response(response)


class SchoolGradeView(generics.ListAPIView):
    queryset = SchoolGrade.objects.all()
    serializer_class = SchoolGradeSerializer
    permission_classes = [AllowAny]


class PlayerRoster(generics.ListAPIView):
    serializer_class = RosterSerializer

    def get_queryset(self):
        if self.request.user.user_role == "player":
            rosters = Roster.objects.filter(
                roster_player__player=self.request.user
            ).distinct()
        else:
            rosters = Roster.objects.filter(
                roster_coach__coach=self.request.user
            ).distinct()

        return rosters

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["player"] = self.request.user
        return context


class RosterExitRequestView(APIView):
    # permission_classes = [IsPlayerUser]
    serializer_class = RosterRequestSerializer

    def put(self, request):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            roster = data.validated_data['roster']

            if RosterPlayer.objects.filter(roster=roster, player=request.user).exists() is False:
                return Response({
                    "detail": "You are not able to perform this action because you are not member of this roster"
                }, status=status.HTTP_400_BAD_REQUEST)

            request_obj = RosterExitRequest.objects.create(
                roster=roster,
                user=request.user
            )

            roster_creator = roster.organization.created_by

            send_single_user_admin_notification.delay(
                username=roster_creator.username,
                user_id=roster_creator.id,
                title="Roster exit request",
                message=f"{request.user.get_full_name().title()} has request to exit roster {roster.name.title()}.",
                action="roster_exit",
                is_action=True,
                object_id=request_obj.id
            )
            return Response({"detail": "Request successfully sent to coach."})


