import json
import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.db.models import Count, F, Value, IntegerField, Func
from django.db.models.functions import Coalesce
from django.db.models import Sum
from datetime import datetime, timedelta
from coach.api.services import IsCoachUser
from event.models import Event, EventFollower, EventCheckIn, EventPlan, EventTransaction
from event.services.paypal_checkout_session import paypal_checkout_session
from users.models import User
from users.serializers import UserSerializer
from .serializers import EventFollowSerializer, EventCheckInSerializer, EventPlanSerializer, EventCheckedInSerializer
from .serializers.event import EventSerializer, EventTeamSerializer, EventLeaderBoardSerializer, RosterSubmitSerializer
from coach.api.services import IsCoachOrPlayer
from users.models import VerificationTransaction
from users.services import send_parent_verification_mail
from coach.models import OrganizationTransaction
from dashboard.models import AdminSubscriptionTransaction, AdminSubscription
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models.functions import Cast
from django.db.models import CharField
from django.db.models import Case, When, Value, IntegerField
from users.models.discount_management import DiscountCodeUsage


class EventAPIView(generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = EventSerializer
    # queryset = Event.objects.select_related('user').filter(is_active=True, is_deleted=False)
    pagination_class = None

    def get(self, request, *args, **kwargs):
        event_id = request.query_params.get('event_id', )
        event_type = request.query_params.get("event_type")
        query = request.query_params.get("q", "")
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                serializer = self.get_serializer(event, context={"request": request})
                return Response(serializer.data)
            except Event.DoesNotExist:
                raise NotFound({"error": "Event not found"})

        now = timezone.now()

        queryset = Event.objects.select_related('user').filter(
            is_active=True
        ).annotate(
            is_upcoming=Case(
                When(
                    Q(date__gte=now) | Q(date__lte=now, end_date__gte=now),
                    then=Value(0)
                ),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('is_upcoming', 'date')

        if event_type and event_type not in ["admin", 'ar']:
            return Response({"detail": "Invalid event type select admin or ar."}, status=status.HTTP_400_BAD_REQUEST)

        elif event_type == "admin":
            queryset = queryset.filter(
                Q(user__user_role="admin") | Q(user__user_role="sub-admin") | Q(user__is_staff=True))

        elif event_type == "ar":
            queryset = queryset.exclude(
                Q(user__user_role="admin") | Q(user__user_role="sub-admin") | Q(user__is_staff=True))

        if query:
            queryset = queryset.annotate(
                date_str=Cast('date', CharField())
            ).filter(
                Q(name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(date_str__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query) |
                Q(teams__name__icontains=query) |
                Q(rosters__name__icontains=query)
            ).distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context={"request": request}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context={"request": request}, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsCoachUser()]

    def patch(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": "Invalid event id please check the url"
            })
        instance = self.get_object()
        serializer = self.serializer_class(instance=instance, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(data={
                "detail": "Event update successfully."
            })

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": "Invalid event id please check the url"
            })
        event = Event.objects.filter(id=pk, user=request.user).first()
        if not event:
            return Response(status=status.HTTP_404_NOT_FOUND, data={
                "detail": "Event does not exit."
            })
        event.delete()
        return Response(status=status.HTTP_200_OK, data={
            "detail": "Event deleted successfully."
        })

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            event_type = serializer.validated_data.get('event_type')

            plan = serializer.validated_data.get('plan')

            if not plan and event_type != 'free':
                return Response(data={
                    'detail': "Plan missing please select."
                }, status=status.HTTP_400_BAD_REQUEST)

            elif event_type != 'free':
                serializer.validated_data.pop('plan')
                event = serializer.save(user=request.user)
                event.is_active = False
                event.save()
                payment_response = paypal_checkout_session(plan, request.user, event)
                return Response(payment_response)

            event = serializer.save(user=request.user)
            serialize = self.serializer_class(event, context={"request": request})
            return Response(data={
                "detail": "Event created successfully.",
                "data": serialize.data
            }, status=status.HTTP_201_CREATED)


class EventFollow(APIView):
    serializer_class = EventFollowSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):

            event_follow = EventFollower.objects.filter(
                event=serializer.validated_data['event'],
                user=request.user
            )

            if event_follow.exists():
                event_follow.delete()
                return Response(data={"detail": "Event unfollow successfully."})

            EventFollower.objects.create(
                event=serializer.validated_data['event'],
                user=request.user
            )
            return Response(data={"detail": "Event follow successfully."})

    def get(self, request, *args, **kwargs):
        event_id = self.request.query_params.get("id", '')
        if not event_id:
            return Response({"detail": "Invalid event id"}, status=status.HTTP_400_BAD_REQUEST)

        # event_followers = EventFollower.objects.select_related("event", "user").filter(event__id=event_id)
        users = User.objects.filter(eventfollower__event_id=event_id)
        serialize = UserSerializer(users, context={'request': request}, many=True)
        return Response({
            "detail": "Follower fetch successfully of event.",
            "data": serialize.data
        })


class CoachEvent(generics.ListAPIView):
    permission_classes = [IsCoachUser]
    serializer_class = EventSerializer

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        queryset = Event.objects.select_related("user").filter(user=self.request.user)
        queryset = queryset.annotate(
            date_str=Cast('date', CharField())
        ).filter(
            Q(name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(date_str__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(teams__name__icontains=query) |
            Q(rosters__name__icontains=query)
        )
        return queryset


class EventTypes(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        EventTypesRes = [i[0] for i in Event.EVENT_TYPE_CHOICES]
        return Response({
            "detail": "Event types fetched successfully",
            "data": EventTypesRes
        }
        )


class EventCheckInRosterUser(APIView):

    def get(self, request, *args, **kwargs):
        event_id = kwargs['event_id']
        event = get_object_or_404(Event, is_deleted=False, id=event_id)
        if event.end_date:
            is_ended = event.end_date < timezone.now()
        else:
            is_ended = event.date < timezone.now()

        if is_ended:
            return Response({"detail": "This event has already ended, you can't check in.", },
                            status=status.HTTP_400_BAD_REQUEST)
        elif request.user.is_identity_verified is False:
            return Response({
                "detail": "Account verification is required. Please verify your account before checking in to any "
                          "event."
            }, status=status.HTTP_400_BAD_REQUEST)

        checkin_obj = EventCheckIn.objects.filter(user=request.user, event=event)
        if checkin_obj.exists():
            serialize = EventCheckedInSerializer(checkin_obj.first(), context={"user": request.user}).data
            serialize['detail'] = "Your checkin detail fetched successfully"
            serialize["status"] = True
            return Response(serialize)

        rosters = event.rosters.all()
        for i in rosters:
            is_roster_user = i.roster_player.filter(player=request.user).exists()
            is_roster_coach = i.roster_coach.filter(coach=request.user).exists()
            if is_roster_user or is_roster_coach:
                EventCheckIn.objects.create(
                    user=request.user,
                    event=event,
                    squad=i.name,
                    roster=i
                )
                verification = request.user.verification.filter(status="accept").first()

                return Response(
                    {
                        "detail": f"You have checked in successfully to roster {i.name}.",
                        "status": True,
                        "roster": i.name,
                        "verified_pic": verification.photo.url if verification and verification.photo else ""
                    }
                )

        return Response(
            {"detail": f"You could not be found in any roster. Please select a team and submit to check in.",
             "status": False})


class EventCheckInView(APIView):
    permission_classes = [IsCoachOrPlayer]

    def post(self, request, *args, **kwargs):
        serializer = EventCheckInSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            if not request.user.is_identity_verified:
                return Response(
                    {
                        "detail": "Your identity has not been verified yet. Please complete"
                                  " verification before checking in to the event.",
                        "code": "IDENTITY_NOT_VERIFIED",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if EventCheckIn.objects.select_related("event", "user").filter(user__id=request.user.id,
                                                                           event__id=serializer.validated_data[
                                                                               'event'].id).exists():
                return Response({"detail": f"{request.user.first_name} you have already checked in."},
                                status=status.HTTP_400_BAD_REQUEST)

            team = serializer.validated_data.get("team")
            EventCheckIn.objects.create(
                user=request.user,
                event=serializer.validated_data['event'],
                jersey_number=serializer.validated_data['jersey_number'],
                squad=team.name if team else "",
                team=team
            )
            return Response({"data": "You have checked in successfully."})


class EventPlanView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EventPlanSerializer
    pagination_class = None
    queryset = EventPlan.objects.filter(is_active=True, is_deleted=False)

    def get(self, request, *args, **kwargs):
        free_plan = self.serializer_class(self.queryset.filter(name="free"), many=True)
        ar_plans = self.serializer_class(self.queryset.exclude(name="free"), many=True)
        return Response({
            "detail": "fetch successfully",
            "free_plans": free_plan.data,
            "ar_plans": ar_plans.data
        })


class PaymentWebhook(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def get_paypal_access_token():
        """
        Get OAuth2 access token from PayPal
        """
        url = f"{settings.PAYPAL_API_BASE}/v1/oauth2/token"

        response = requests.post(
            url,
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
        )

        if response.status_code != 200:
            raise Exception(f"PayPal token request failed: {response.text}")

        return response.json()["access_token"]

    def post(self, request, *args, **kwargs):
        payload = request.body
        headers = request.headers

        verify_url = f"{settings.PAYPAL_API_BASE}/v1/notifications/verify-webhook-signature"

        access_token = self.get_paypal_access_token()

        verify_payload = {
            "transmission_id": headers.get("Paypal-Transmission-Id"),
            "transmission_time": headers.get("Paypal-Transmission-Time"),
            "cert_url": headers.get("Paypal-Cert-Url"),
            "auth_algo": headers.get("Paypal-Auth-Algo"),
            "transmission_sig": headers.get("Paypal-Transmission-Sig"),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": json.loads(payload),
        }

        response = requests.post(
            verify_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            json=verify_payload,
        )

        verification_status = response.json().get("verification_status")
        if verification_status != "SUCCESS":
            return JsonResponse({"error": "Invalid webhook signature"}, status=400)

        event = json.loads(payload)
        event_type = event.get("event_type")

        if event_type == "CHECKOUT.ORDER.APPROVED" or "APPROVED" in event_type:
            order_id = event["resource"]["id"]
            resource = event.get("resource", {})
            payer_info = resource.get("payer", {})

            # Capture the payment
            auth_response = requests.post(
                f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
                data={"grant_type": "client_credentials"},
            )
            access_token = auth_response.json().get("access_token")

            capture_response = requests.post(
                f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                },
            )

            capture_data = capture_response.json()
            print("Webhook Capture:", capture_data)

            transaction = EventTransaction.objects.filter(
                session_id=order_id
            ).first()

            if transaction:
                # Update payment details
                transaction.status = "succeeded"
                transaction.payer_info = payer_info
                transaction.save()
                event = transaction.event
                event.is_active = True
                event.save()

            # elif VerificationTransaction.objects.filter(session_id=order_id).first():
            #     verification_obj = VerificationTransaction.objects.filter(session_id=order_id).first()
            #     verification_obj.status = "succeeded"
            #     verification_obj.payer_info = payer_info
            #     verification_obj.save()
            #     verification = verification_obj.verification
            #     verification.status = "pending"
            #     verification.is_active = True
            #     verification.save()
            #     try:
            #         send_parent_verification_mail(verification_obj.verification)
            #     except:
            #         pass

            elif VerificationTransaction.objects.filter(session_id=order_id).first():
                verification_obj = VerificationTransaction.objects.filter(session_id=order_id).first()
                verification_obj.status = "succeeded"
                verification_obj.payer_info = payer_info
                verification_obj.save()

                verification = verification_obj.verification
                if verification.status in ["expired", "expiring"]:
                    verification.status = "accept"
                else:
                    verification.status = "pending"
                    verification.is_active = True
                verification.save(update_fields=["status", "is_active"])

                # add new code second feb
                verification = verification_obj.verification
                if verification and verification.discount:
                    discount = verification.discount
                    discount.current_usage += 1
                    discount.save(update_fields=["current_usage"])
                    DiscountCodeUsage.objects.get_or_create(
                        user=verification_obj.user,
                        discount=discount
                    )
                try:
                    send_parent_verification_mail(verification_obj.verification)
                except:
                    pass

            elif OrganizationTransaction.objects.filter(session_id=order_id).exists():
                org_transaction = OrganizationTransaction.objects.filter(session_id=order_id).first()
                org_transaction.status = "succeeded"
                org_transaction.payer_info = payer_info
                org_transaction.save()
                org = org_transaction.organization
                org.is_active = True
                org.save()

            elif AdminSubscriptionTransaction.objects.filter(session_id=order_id).exists():
                transaction = AdminSubscriptionTransaction.objects.get(session_id=order_id)
                transaction.status = "succeeded"
                transaction.payer_info = payer_info
                transaction.save()

                # create user subscription
                AdminSubscription.objects.create(
                    user=transaction.user,
                    start_date=datetime.now().date(),
                    end_date=datetime.now().date() + timedelta(days=30),
                    transaction=transaction
                )

            else:
                print("No found for session", order_id)

        elif event_type == "payment_intent.payment_failed" or event_type == "CHECKOUT.ORDER.DECLINED":
            order_id = event["resource"]["id"]
            transaction = EventTransaction.objects.filter(
                session_id=order_id
            ).first()

            if transaction:
                transaction.payment_status = "failed"
                transaction.save()

            elif VerificationTransaction.objects.filter(session_id=order_id).first():
                verification_obj = VerificationTransaction.objects.filter(session_id=order_id).first()
                verification_obj.status = "failed"
                verification_obj.save()

            elif OrganizationTransaction.objects.filter(session_id=order_id).exists():
                org_transaction = OrganizationTransaction.organization.filter(session_id=order_id).first()
                org_transaction.status = "failed"
                org_transaction.save()

            elif AdminSubscriptionTransaction.objects.filter(session_id=order_id).exists():
                transaction = AdminSubscriptionTransaction.objects.get(session_id=order_id)
                transaction.status = "failed"
                transaction.save()

        return Response(data={"details": "ok"}, status=200)


class EventRepayment(APIView):

    def get(self, request, *args, **kwargs):
        event = Event.objects.filter(
            id=kwargs['id'],
            user=request.user
        ).first()

        if not event:
            return Response(
                data={"detail": "Invalid event not found."}
            )

        elif event.is_active:
            return Response(
                data={"detail": "Your event is already active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction = EventTransaction.objects.filter(event=event, user=request.user).first()
        payment_response = paypal_checkout_session(transaction.event_plan, request.user, event)
        return Response(payment_response)


class EventTeam(APIView):
    serializer_class = EventTeamSerializer
    permission_classes = [IsCoachOrPlayer]

    def get(self, request, *args, **kwargs):
        event = Event.objects.filter(id=kwargs['id']).first()
        if not event:
            return Response(data={
                "detail": "invalid event id pls check"
            }, status=status.HTTP_400_BAD_REQUEST)

        teams = event.teams.all()
        serialize = self.serializer_class(teams, many=True)
        return Response(data={
            "detail": "Team fetch successfully",
            "data": serialize.data
        })


class ArrayLength(Func):
    function = "CARDINALITY"
    output_field = IntegerField()


class EventLeaderBoard(APIView):
    serializer_class = EventLeaderBoardSerializer

    def get(self, request, *args, **kwargs):
        event_id = kwargs['event_id']
        checkin_users = (
            User.objects.filter(
                user_role="player",
                event_check_in__event_id=event_id
            )
            .select_related("player")
            .annotate(
                overall_rating=F("player__overall_rating"),
                badge_count=Count("badge", distinct=True),
                template_count=Coalesce(
                    Sum(ArrayLength("badge__templates")),  # sum of array lengths
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
            .order_by("-badge_count", "-overall_rating", "-template_count")
            .distinct()
        )

        users = list(checkin_users)
        rank_map = {}
        team_names = {}
        for i, user in enumerate(users, start=1):
            team = user.event_check_in.filter(event__id=event_id).first().squad
            rank_map[user.id] = i
            team_names[user.id] = team.title() if team else ""

        serialize = self.serializer_class(checkin_users, many=True,
                                          context={"rank_map": rank_map, "team_names": team_names})
        return Response({
            "detail": "Leaderboard fetch successfully",
            "total_players": checkin_users.count(),
            "data": serialize.data
        })


def paypal_capture_payment(request):
    try:
        order_id = request.GET.get("token")
        if not order_id:
            return JsonResponse({"detail": "Missing order ID"}, status=400)

        # Get Access Token
        auth_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
        )
        access_token = auth_response.json().get("access_token")

        # Capture the payment
        capture_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        capture_data = capture_response.json()
        print("CAPTURE RESPONSE:", capture_data)

        # Verify payment success
        if capture_data.get("status") == "COMPLETED":
            EventTransaction.objects.filter(session_id=order_id).update(
                status="succeeded"
            )
            return JsonResponse({"detail": "Payment completed successfully!"})
        else:
            EventTransaction.objects.filter(session_id=order_id).update(
                status="failed"
            )
            return JsonResponse({
                "detail": "Payment not completed",
                "response": capture_data,
            }, status=400)

    except Exception as e:
        print("PAYPAL CAPTURE ERROR:", e)
        return JsonResponse({"detail": f"Failed to capture payment: {str(e)}"}, status=400)


class RosterSubmission(APIView):

    def post(self, request, *args, **kwargs):
        serializer = RosterSubmitSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            rosters = serializer.validated_data['rosters']
            event = serializer.validated_data['event']
            for roster in rosters:
                event.rosters.add(roster)
            return Response({"detail": "Roster submitted successfully."})
