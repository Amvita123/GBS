from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializer import OneToOneSimulationSerializer, FiveToFiveSimulationSerializer, FiveTOFivePlayerSimulation, \
    CoachTypeSerializer
from .services import IsCoachUser
from .utils import coach_5vs5_simulation, coach_5vs5_player_simulation
from players.api.serializers.squad import SquadSerializer
from players.models import Squad
from users.serializers import UserSerializer
from coach.models import *
from coach.models import CoachType, Organization, InvitePlayer, Roster, RosterGrade
from rest_framework.permissions import AllowAny, IsAuthenticated
from coach.api import serializer
from . import services
from notification.task import send_single_user_admin_notification
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404


class OneToOneSimulation(APIView):
    serializer_class = OneToOneSimulationSerializer
    permission_classes = [IsCoachUser]

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            player_1 = (9 - data.validated_data['player_1'].player_profile.position.rating) * (
                    21 - data.validated_data['player_1'].player_profile.playing_style.archetype_rating)
            player_2 = (9 - data.validated_data['player_2'].player_profile.position.rating) * (
                    21 - data.validated_data['player_2'].player_profile.playing_style.archetype_rating)

            if player_1 > player_2:
                message = f"{data.validated_data['player_1'].username} wins."
            else:
                message = f"{data.validated_data['player_2'].username} wins."

            return Response({
                "status": message,
                "player_1": player_1,
                "player_2": player_2
            })


class FiveVsFiveSimulation(APIView):
    permission_classes = [IsCoachUser]

    def post(self, request):
        data = FiveToFiveSimulationSerializer(data=request.data)
        if data.is_valid(raise_exception=True):
            squad_1 = data.validated_data['squad_1']
            squad_2 = data.validated_data['squad_2']
            winner = coach_5vs5_simulation(squad_1, squad_2)
            return Response({"status": winner}, status=status.HTTP_200_OK)


class SquadView(generics.ListAPIView):
    serializer_class = SquadSerializer
    permission_classes = [IsCoachUser]

    # def get_queryset(self):
    #     squad_id = self.request.query_params.get("id", None)
    #     if squad_id:
    #         queryset = self.queryset.filter(id=squad_id)
    #         if queryset:
    #             return queryset
    #
    #     return self.queryset

    def get(self, request, *args, **kwargs):
        from rest_framework.pagination import PageNumberPagination
        squad_id = self.request.query_params.get("id", None)
        queryset = Squad.objects.filter(is_active=True)
        if squad_id:
            queryset = queryset.filter(id=squad_id).first()
            if queryset:
                serialize = self.serializer_class(queryset)
                return Response(serialize.data)
            else:
                return Response({"detail": "invalid squad not found."}, status=status.HTTP_404_NOT_FOUND)
        paginator = PageNumberPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)

        serialize = self.serializer_class(paginated_qs, many=True)
        return paginator.get_paginated_response(serialize.data)


class FiveVsFivePlayer(APIView):
    permission_classes = [IsCoachUser]

    def post(self, request, *args, **kwargs):
        serializer = FiveTOFivePlayerSimulation(data=request.data)
        if serializer.is_valid(raise_exception=True):
            winner = coach_5vs5_player_simulation(
                first_group=serializer.validated_data['players_group_1'],
                second_group=serializer.validated_data['players_group_2'],
            )
            players_group_1 = UserSerializer(serializer.validated_data['players_group_1'], many=True,
                                             context={'request': request})
            players_group_2 = UserSerializer(serializer.validated_data['players_group_2'], many=True,
                                             context={'request': request})
            return Response({
                "status": winner,
                "players_group_1": players_group_1.data,
                "players_group_2": players_group_2.data,
            })


class CoachTypeView(generics.ListAPIView):
    queryset = CoachType.objects.all()
    serializer_class = CoachTypeSerializer
    permission_classes = [AllowAny]


class OrganizationView(generics.CreateAPIView):
    serializer_class = serializer.OrganizationSerializer
    permission_classes = [IsCoachUser]

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            if request.user.is_identity_verified is False:
                return Response(
                    {
                        "detail": "You can’t create an organization until your account is verified. Please verify your account first."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Organization.objects.filter(created_by=request.user, is_active=True).count() >= 4:
                return Response(
                    data={
                        "detail": "You have already created 4 organizations. You cannot create more."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            is_paid = False

            org = data.save(created_by=request.user, is_active=False if is_paid is True else True)
            if is_paid:
                paypal_url = services.organization_paypal_checkout_session(25, request.user, org)
            else:
                paypal_url = {
                    "detail": "Your Organization created successfully.",
                    "id": "",
                    "link": ""
                }
            paypal_url['is_paid'] = is_paid
            return Response(
                paypal_url
            )

    def get(self, request, *args, **kwargs):
        name = self.request.query_params.get("q")
        pk = self.request.query_params.get("id")

        organizations = Organization.objects.filter(created_by=request.user, is_active=True)
        if name:
            organizations = organizations.filter(name__icontains=name, is_active=True)

        if pk:
            organization = organizations.filter(id=pk).first()
            if not organization:
                return Response({
                    "detail": "Invalid id organization not found"
                }, status=status.HTTP_404_NOT_FOUND)
            serialize = self.serializer_class(organization)

        else:
            serialize = self.serializer_class(organizations, many=True)

        return Response(
            {
                "detail": "Organization fetch successfully",
                "data": serialize.data
            }
        )


class AllOrganizationView(generics.ListAPIView):
    serializer_class = serializer.OrganizationListSerializer
    queryset = Organization.objects.filter(is_active=True)

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("q")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class RosterView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = serializer.RosterSerializer

    @staticmethod
    def invite_player(user, roster, from_user_id):
        invitation = InvitePlayer.objects.create(
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            roster=roster
        )
        send_single_user_admin_notification.delay(
            username=user.username,
            user_id=user.id,
            title="Roster Invitation",
            message=f"Roster {roster.name} has invited you to join",
            action="roster_invitation",
            object_id=invitation.id,
            from_user_id=from_user_id,
            is_action=True
        )

    def post(self, request, *args, **kwargs):
        serialize = self.serializer_class(data=request.data)
        if serialize.is_valid(raise_exception=True):
            organization_obj = serialize.validated_data['organization']
            if organization_obj.created_by.id == request.user.id:
                roster = serialize.save()

                # invite players and coach
                def invite_users(users):
                    for usr in users:
                        self.invite_player(
                            user=usr,
                            roster=roster,
                            from_user_id=request.user.id
                        )

                invite_users(serialize.validated_data.get("player"))
                invite_users(serialize.validated_data.get("coach"))
                try:
                    RosterCoach.objects.create(
                        roster=roster,
                        coach=request.user
                    )
                except:
                    pass

                return Response(data={
                    "detail": "Roster created successfully",
                    "data": serialize.data
                }, status=status.HTTP_201_CREATED)

            return Response(
                data={
                    "detail": "please select your organization this organization is associated with other user."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, *args, **kwargs):
        pk = self.request.query_params.get("id")
        if pk:
            roster = Roster.objects.filter(id=pk).first()
            if not roster:
                return Response({
                    "detail": "Roster not found please check id param."
                }, status=status.HTTP_404_NOT_FOUND)
            serialize = self.serializer_class(roster)
            return Response({
                "detail": "Roster fetch successfully",
                "data": serialize.data
            })
        rosters = Roster.objects.select_related("organization").filter(organization__created_by=request.user,
                                                                       organization__is_active=True)
        serialize = serializer.RosterListSerializer(rosters, many=True,
                                                    context={'fields': ['id', 'name', 'organization']})
        return Response({
            "detail": "Roster fetch successfully",
            "data": serialize.data
        })

    def delete(self, request, *args, **kwargs):
        pk = self.request.query_params.get("id")
        try:
            roster = get_object_or_404(
                Roster.objects.only("id", "name"),
                id=pk, organization__created_by_id=request.user.id
            )
        except Exception:
            return Response(
                {"detail": "Roster not found or you do not have permission to delete it.", "code": "NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND
            )

        roster_name = roster.name
        roster.delete()
        return Response({"detail": f"{roster_name} has been deleted successfully.", "code": "SUCCESS"})


class InvitePlayerView(generics.CreateAPIView):
    serializer_class = serializer.InvitePlayerSerializer
    permission_classes = [IsCoachUser]

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            from .utils import send_roster_invitation_mail
            invitation_obj = data.save()
            send_roster_invitation_mail(invitation_obj, request.user.get_full_name())
            return Response({
                "detail": "Player invited to this roster"
            })


class InviteAppPlayerView(APIView):

    def post(self, request, *args, **kwargs):
        data = serializer.InviteAppPlayerSerializer(data=request.data)
        if data.is_valid(raise_exception=True):
            user = data.validated_data['user']
            roster = data.validated_data['roster']

            try:
                if user.player:
                    if int(roster.grade.name) > int(user.player.grade.name):
                        return Response({
                            "detail": f"Player {user.first_name} can not able to join because those teams are younger than the player."
                        }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)

            invitation = InvitePlayer.objects.create(
                name=f"{user.first_name} {user.last_name}",
                email=user.email,
                roster=data.validated_data['roster']
            )
            send_single_user_admin_notification.delay(
                username=user.username,
                user_id=user.id,
                title="Roster Invitation",
                message=f"Roster {data.validated_data['roster'].name} has invited you to join",
                action="roster_invitation",
                object_id=invitation.id,
                is_action=True
            )

            return Response({
                "detail": "Player Invited successfully"
            })


class RosterInvitationActionView(APIView):

    def post(self, request, *args, **kwargs):
        data = serializer.RosterInvitationActionSerializer(data=request.data)
        if data.is_valid(raise_exception=True):
            notification = data.validated_data['notification']

            invitation = InvitePlayer.objects.filter(id=notification.objects_id).first()
            if not invitation:
                return Response({"detail": "Invalid invitation we could not found."}, status=status.HTTP_404_NOT_FOUND)

            elif not request.user.is_identity_verified:
                return Response({"detail": "Please verify your identity before joining any roster."},
                                status=status.HTTP_400_BAD_REQUEST)

            roster = invitation.roster

            try:
                if int(roster.grade.name) > int(request.user.player.grade.name):
                    return Response({
                        "detail": f"Player {request.user.first_name} can not able to join because those teams are younger than the player."
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)

            if invitation.email != request.user.email:
                return Response(
                    {
                        "detail": "Invalid invitation we could not recognize you make user you login and invitation "
                                  "mail same."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if data.validated_data['action'] == "accept":
                create_data = {"roster": roster, "player": request.user}
                try:
                    if request.user.user_role == "player":
                        RosterPlayer.objects.create(
                            **create_data
                        )
                    else:
                        if RosterCoach.objects.select_related("roster").filter(roster__id=roster.id).count() == 4:
                            return Response({
                                "detail": "The roster’s coach positions are full; you cannot join."
                            }, status=status.HTTP_400_BAD_REQUEST)

                        create_data = {"roster": roster, "coach": request.user}
                        RosterCoach.objects.create(
                            **create_data
                        )
                except Exception as e:
                    return Response(
                        {
                            "detail": "Your have already perform action.",
                            "error": str(e)
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                roster.save()
                invitation.status = "accept"
                notification.message = notification.message + " - You have accepted."

            else:
                invitation.status = "reject"
                notification.message = notification.message + " - You have rejected."

            # send notification to coach
            try:
                send_single_user_admin_notification.delay(
                    username=roster.organization.created_by.username,
                    user_id=roster.organization.created_by.id,
                    title="Roster Invitation",
                    message=f"{request.user.username.title()} has {data.validated_data['action']}ed the invitation to join roster {roster.name}",
                    is_action=False,
                    from_user_id=request.user.id
                )
            except Exception as e:
                print(e)

            notification.is_action = False
            notification.save()
            invitation.save()
            return Response({
                "detail": f"You {data.validated_data['action']}ed successfully"
            })


class RosterGradeView(generics.ListAPIView):
    serializer_class = serializer.RosterGradeSerializer
    queryset = RosterGrade.objects.all()
    pagination_class = None


class AssignJerseyNumber(APIView):
    serializer_class = serializer.AssignJerseyNumberSerializer

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            roster = data.validated_data['roster']
            user = data.validated_data['user']

            if roster.organization.created_by.id != request.user.id:
                return Response(
                    data={
                        "detail": "please select your organization this organization is associated with other user."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.user_role == "player":
                roster_user = RosterPlayer.objects.select_related("roster", "player").filter(roster=roster,
                                                                                             player=user).first()
            else:
                roster_user = RosterCoach.objects.select_related("roster", "player").filter(roster=roster,
                                                                                            player=user).first()

            roster_user.jersey_number = data.validated_data['jersey_number']
            if data.validated_data.get("position"):
                roster_user.position = data.validated_data.get("position")
            roster_user.save()

            return Response({"detail": "Jersey assign successfully."})


@api_view(['DELETE'])
def delete_roster_user(request):
    roster_id = request.query_params.get('roster_id')
    user_id = request.query_params.get('user_id')

    if not roster_id or not user_id:
        return Response(
            {"detail": "roster_id and user_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    roster = Roster.objects.filter(id=roster_id).first()

    if not roster:
        return Response(
            {"detail": "Invalid roster not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if roster.organization.created_by.id != request.user.id:
        return Response(
            data={
                "detail": "You don't have permission to perform this action."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    roster_player = roster.roster_player.filter(player__id=user_id)
    roster_coach = roster.roster_coach.filter(coach__id=user_id)

    if roster_coach.exists() is False and roster_player.exists() is False:
        return Response(
            data={
                "detail": "User does not found on this roster."
            },
            status=status.HTTP_404_NOT_FOUND
        )
    if roster_player.exists():
        roster_player.delete()
        return Response({"detail": f"Player has been deleted successfully from {roster.name.title()}"})

    elif roster_coach.exists():
        roster_coach.delete()
        return Response({"detail": f"Coach has been deleted successfully from {roster.name.title()}"})

    return Response({"detail": f"Something you went wrong"}, status=status.HTTP_400_BAD_REQUEST)


class HandlerRosterExit(APIView):
    permission_classes = [IsCoachUser]
    serializer_class = serializer.HandlerRosterExitSerializer

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            notification = data.validated_data['notification']
            action = data.validated_data['action']

            request_obj = RosterExitRequest.objects.filter(id=notification.objects_id).first()
            if not request_obj:
                return Response({"detail": "Invalid request we could not found."}, status=status.HTTP_404_NOT_FOUND)

            if request_obj.user.user_role == "player":
                user_roster = RosterPlayer.objects.filter(roster=request_obj.roster, player=request_obj.user)
            else:
                user_roster = RosterCoach.objects.filter(roster=request_obj.roster, coach=request_obj.user)

            if user_roster.exists() is False:
                return Response(
                    {"detail": "User not found on this roster."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if action == "accept":
                user_roster.delete()
                notification.message = notification.message + " - You have accepted."
            else:
                notification.message = notification.message + " - You have rejected."

            notification.is_action = False
            notification.save()

            send_single_user_admin_notification.delay(
                username=request_obj.user.username,
                user_id=request.user.id,
                title=f"Roster exit request {action}ed successfully.",
                message=f"{request.user.get_full_name().title()} has {action}ed your request: roster {request_obj.roster.name.title()}."
            )

            return Response({"detail": "Action performed successfully."})
