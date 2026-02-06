from rest_framework import generics, status, exceptions
from rest_framework.response import Response
from users.serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.services import send_otp_to_mail, send_forget_password_otp, UserProfileFilter, FollowingFilter, \
    FollowerFilter, verification_paypal_checkout_session, send_parent_verification_mail
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes
from users.models import *
from users.models import User, BlockUser, VerificationTransaction
from django.db.models import Q
from players.models import Follow
from players.api.serializers.signup import PlayerSignUp as PlayerSignUpSerializer
from notification.models import FCMToken
from rest_framework.views import APIView
from notification.task import send_user_action_notification, manual_user_invitation_notification
import requests
from jwt import PyJWKClient
import jwt
from django.utils.text import slugify
from users.serializers.verification import *
from common.models.project_settings import ProjectSettings
# from users.constants import VERIFICATION_STATUS_MESSAGES
from django.db import transaction
from users.models.discount_management import DiscountCode
from users.serializers.discount_serializer import ValidateDiscountCodeSerializer
from users.services.verification import get_discounted_amount_value


# from users.serializers.discount_serializer import DiscountCodeSerializer, ApplyDiscountSerializer


class UserSignUp(generics.CreateAPIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email= request.data.get('email').lower()
        user_exists = User.objects.filter(email=email).first()
        if user_exists and not user_exists.is_verified:
            send_otp_to_mail(username=f'{user_exists.first_name} {user_exists.last_name}', user_email=user_exists.email.lower(),
                             phone_number=user_exists.phone_number)

            return Response({
                "status": ["Please verify otp"]
            }, status=status.HTTP_200_OK)

        if user_exists and user_exists.is_verified:
            return Response({"status": ["An account is already registered with this email address. Please proceed to login."]}, status=status.HTTP_400_BAD_REQUEST)

        if request.data.get("user_role") == "player":
            data = PlayerSignUpSerializer(data=request.data)
        else:
            data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            try:
                fcm_token_data = data.validated_data.pop("fcm", None)
            except Exception as e:
                print(e)
                fcm_token_data = None

            usr = data.save()
            if request.data.get("user_role") != "player":
                usr.set_password(data.validated_data['password'])
            usr.is_active = True
            usr.save()
            send_otp_to_mail(username=f'{usr.first_name} {usr.last_name}', user_email=usr.email.lower(),
                             phone_number=usr.phone_number)

            if fcm_token_data:
                SignIn.handle_fcm_token(
                    user=usr,
                    fcm_data=fcm_token_data,
                    request=request
                )
            serialize = UserSerializer(usr)
            return Response({"status": "Register successfully", "data": serialize.data})


class OtpVerification(generics.CreateAPIView):
    serializer_class = OtpVerificationSerializer
    permission_classes = [AllowAny]

    @staticmethod
    def follow_admin_coach(user):
        try:
            admin_user = User.objects.filter(Q(email="taylor@yopmail.com") | Q(email="anitasdavis@gmail.com")).first()
            data = {
                "following": admin_user,
                "follower": user
            }
            follow = Follow.objects.filter(**data)
            if follow.exists() is False:
                Follow.objects.create(
                    **data
                )
        except:
            pass

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid(raise_exception=True):
            user = data.validated_data['user']
            resend = self.request.query_params.get("resend")

            if user.is_verified is True:
                return Response({
                    "status": "your account is already verified"
                }, status=status.HTTP_400_BAD_REQUEST)

            if str(resend).lower() == "true":
                send_otp_to_mail(username=f'{user.first_name} {user.last_name}', user_email=user.email,
                                 phone_number=user.phone_number)
                return Response({"status": "OTP send successfully"})

            cache_otp = cache.get(f"otp_{user.email}")
            if cache_otp is None:
                send_otp_to_mail(username=f'{user.first_name} {user.last_name}', user_email=user.email,
                                 phone_number=user.phone_number)
                return Response({"otp": "your previous opt was expired. we have resend otp please check your mail."},
                                status=status.HTTP_404_NOT_FOUND)

            if cache_otp == data.validated_data['otp']:
                user.is_verified = True
                user.save()
                refresh = RefreshToken.for_user(user)
                serialize = UserSerializer(user)
                self.follow_admin_coach(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_info': serialize.data
                })

                # return Response({"status": "otp verified successfully"})
            return Response({"otp": "invalid otp please check"},
                            status=status.HTTP_400_BAD_REQUEST)


class UserProfile(generics.ListAPIView, generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = UserSerializer
    filterset_class = UserProfileFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff is True or user.user_role == "admin":
            return User.objects.all()

        blocker_ids = BlockUser.objects.filter(blocked=user).values_list('blocker_id', flat=True)

        return User.objects.filter(is_active=True).exclude(
            Q(id=self.request.user.id) |
            Q(is_superuser=True) |
            Q(user_role="admin") |
            Q(id__in=blocker_ids)
        )

    def get(self, request, *args, **kwargs):

        if self.request.query_params:
            return self.list(request, *args, **kwargs)

        serialize = UserSerializer(request.user, context={'request': request})
        return Response(serialize.data)

    def patch(self, request, *args, **kwargs):
        if request.user.user_role == "player":
            serializer = PlayerSignUpSerializer(request.user, data=request.data, partial=True)
        else:
            serializer = self.serializer_class(request.user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(self.serializer_class(request.user).data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response({"status": "account deleted successfully"})


class ChangePassword(generics.CreateAPIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            if request.user.check_password(serializer.validated_data["current_password"]):
                user = request.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({"status": "password changed successfully"})

            return Response(
                {"current_password": "Incorrect current password."},
                status=status.HTTP_400_BAD_REQUEST
            )


class SignIn(generics.CreateAPIView):
    serializer_class = SignInSerializer
    permission_classes = [AllowAny]

    @staticmethod
    def handle_fcm_token(user, fcm_data, request):
        pre_stored_token = FCMToken.objects.select_related("user").filter(user=user)
        if pre_stored_token.exists():
            pre_stored_token.delete()

        if fcm_data.get("device_type") is None or fcm_data.get("device_type") == "":
            fcm_data['device_type'] = request.user_agent.device.family

        if fcm_data.get("os") is None or fcm_data.get("os") == "":
            fcm_data['os'] = request.user_agent.os

        if fcm_data.get("browser") is None or fcm_data.get("browser") == "":
            fcm_data['browser'] = request.user_agent.browser.family

        FCMToken.objects.create(
            user=user,
            **fcm_data
        )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            password = serializer.validated_data['password']
            user = serializer.validated_data['user']
            user = authenticate(username=user.username, password=password)
            if user:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                if serializer.validated_data.get("fcm") is not None:
                    self.handle_fcm_token(user, serializer.validated_data.get("fcm"), request)
                serialize = UserSerializer(user)

                if user.is_verified is False:
                    return Response({
                        'user_info': serialize.data
                    })

                # check is he/she invited for roster
                manual_user_invitation_notification.delay(
                    email=user.email
                )

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_info': serialize.data
                })

            return Response({
                "password": "Password did not match or incorrect"
            }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@permission_classes([AllowAny])
def RequestForgetPassword(request):
    serialize = ForgetPassword(data=request.data)
    if serialize.is_valid(raise_exception=True):
        user = serialize.validated_data['user']
        send_forget_password_otp(fullname=f"{user.first_name} {user.last_name}", user_email=user.email,
                                 phone_number=user.phone_number)
        return Response({"status": " verification mail send successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def ValidateForgetPasswordOTP(request):
    serializer = OtpVerificationSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        user = serializer.validated_data['user']
        resend = request.query_params.get("resend")

        if str(resend).lower() == "true":
            send_forget_password_otp(fullname=f'{user.first_name} {user.last_name}', user_email=user.email,
                                     phone_number=user.phone_number)
            return Response({"status": "OTP send successfully"})

        cache_otp = cache.get(f"forget_otp_{user.email}")
        if cache_otp == serializer.validated_data['otp']:
            cache.set(f"forget_verified_{user.email}", True, 60 * 10)
            return Response({"status": "OTP verified successfully"})

        elif cache_otp is None:
            send_forget_password_otp(fullname=f'{user.first_name} {user.last_name}', user_email=user.email,
                                     phone_number=user.phone_number)
            return Response({"status": "OTP has expired resend to your mail please recheck."},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "Invalid OTP please check your mail"},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def ResetPassword(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        user = serializer.validated_data['user']
        if cache.get(f"forget_verified_{user.email}"):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"status": "password set successfully"})
        return Response({"status": "password reset failed please retry"},
                        status=status.HTTP_400_BAD_REQUEST)


class UserFollow(generics.ListCreateAPIView):
    serializer_class = UserFollowSerializer

    def filter_follow(self, action=None, user_id=None):
        user_follow = Follow.objects.all()
        request = self.request
        q = self.request.query_params.get("q")
        filter_set = {"q": q}

        if action is not None:
            if action == "follower":
                data = FollowingFilter(filter_set,
                                       user_follow.filter(following__id=user_id if user_id else request.user.id)).qs
            elif action == "following":
                data = FollowerFilter(filter_set,
                                      user_follow.filter(follower__id=user_id if user_id else request.user.id)).qs
            else:
                return Response({"status": "invalid action."},
                                status=status.HTTP_400_BAD_REQUEST)

            serialize = UserFollowerSerializer(data, many=True, context={"action": action, "request": request})
            return Response({
                "status": "ok",
                "count": data.count(),
                "results": serialize.data
            })

        follower = user_follow.filter(following=request.user)
        following = user_follow.filter(follower=request.user)
        follower_serialize = UserFollowerSerializer(follower, many=True,
                                                    context={"action": "follower"})
        following_serialize = UserFollowerSerializer(following, many=True,
                                                     context={"action": "following"})
        return Response({
            "status": "ok",
            "follower_count": follower.count(),
            "following_count": following.count(),
            "follower": follower_serialize.data,
            "following": following_serialize.data
        })

    def get(self, request, *args, **kwargs):
        action = kwargs.get("action", None)
        user_id = self.request.query_params.get("id", None)
        return self.filter_follow(action=action, user_id=user_id)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            notification_obj = {"action": "user_profile", "sender": request.user.username,
                                "receiver": serializer.validated_data['following'].username,
                                "object_id": ""}

            data = {
                "following": serializer.validated_data['following'],
                "follower": request.user
            }

            if data['following'].is_superuser or data['following'].user_role == "admin":
                return Response(
                    {"status": "you can't able to follow admin"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if serializer.validated_data['following'].username == request.user.username:
                return Response({"status": "you can't follow yourself."},
                                status=status.HTTP_400_BAD_REQUEST)

            follow = Follow.objects.filter(**data)
            if follow.exists() is True:
                follow.delete()
                # notification
                notification_obj['message'] = f"{request.user.username} has unfollowed you."
                send_user_action_notification.delay(
                    **notification_obj
                )
                return self.filter_follow()

            Follow.objects.create(
                **data
            )

            # notification
            notification_obj['message'] = f"{request.user.username} is following you."
            send_user_action_notification.delay(
                **notification_obj
            )

            return self.filter_follow()


class BlockUserView(APIView):
    def post(self, request, *args, **kwargs):
        data = BlockUserSerializer(data=request.data)
        if data.is_valid(raise_exception=True):
            user_blocked = BlockUser.objects.filter(blocker=request.user, blocked=data.validated_data['blocked'])
            if user_blocked.exists() is False:
                BlockUser.objects.create(
                    blocker=request.user, blocked=data.validated_data['blocked']
                )
                return Response({"message": f"{data.validated_data['blocked'].username} blocked successfully"},
                                status=status.HTTP_200_OK)

            user_blocked.delete()
            return Response({"message": f"{data.validated_data['blocked'].username} unblocked successfully"},
                            status=status.HTTP_200_OK)


class SignOut(APIView):

    def post(self, request, *args, **kwargs):
        fcm_tokens = FCMToken.objects.filter(user=request.user)
        fcm_tokens.delete()
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class SocialLogin(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def generate_unique_username(base: str) -> str:
        base_slug = slugify(base)
        username = base_slug
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_slug}{counter}"
            counter += 1

        return username

    @staticmethod
    def google_sign_in(token):
        headers = {
            "Authorization": f"Bearer {token}"
        }
        GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
        response = requests.get(
            GOOGLE_USER_INFO_URL,
            headers=headers
        )
        if not response.ok:
            raise exceptions.AuthenticationFailed("Failed to obtain user info from Google. Please try again.")

        info = response.json()
        return {
            "email": info['email'],
            "first_name": info.get('given_name', None),
            "last_name": info.get("family_name", None),
            "password": info.get("sub")
        }

    @staticmethod
    def apple_sign_in(token):
        APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
        try:
            jwk_client = PyJWKClient(APPLE_KEYS_URL)
            signing_key = jwk_client.get_signing_key_from_jwt(token)

            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="com.avioflai.aviation",
            )

            apple_user_id = decoded_token["sub"]
            email = decoded_token.get("email")

        except Exception as e:
            raise exceptions.AuthenticationFailed(detail=f"Invalid Apple token: {str(e)}")

        if not email:
            raise exceptions.AuthenticationFailed(detail="Email is required from Apple")
        return {}

    def post(self, request, *args, **kwargs):
        serializer = SocialAuthSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            if serializer.validated_data['platform'] == "Google":
                user_info = self.google_sign_in(serializer.validated_data['token'])
            elif serializer.validated_data['platform'] == "Apple":
                user_info = self.apple_sign_in(serializer.validated_data['token'])
                return Response({"detail": "Please try again later we are working on it."},
                                status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(f"Invalid platform {serializer.validated_data['platform']}")

            user = User.objects.filter(email=str(user_info['email']).lower())
            fcm = serializer.validated_data.get("fcm")
            if user.exists() is True:
                user = user.first()

                if fcm:
                    SignIn.handle_fcm_token(user=user, fcm_data=fcm, request=request)

                refresh = RefreshToken.for_user(user)
                serialize = UserSerializer(user)

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_info': serialize.data
                })

            if not serializer.validated_data.get("user_role"):
                return Response({"detail": "Please select your role"})
            data = request.data.copy()
            username = self.generate_unique_username(user_info['email'].split('@')[0])

            data['email'] = user_info['email']
            data['first_name'] = user_info.get("first_name")
            data['last_name'] = user_info.get("last_name")
            data['password'] = user_info.get("password", None)
            data['biograph'] = data.get('biograph') if data.get("biograph") else "Not available"
            data['user_role'] = serializer.validated_data['user_role']
            data['username'] = username

            if request.data.get("user_role") == "player":
                data = PlayerSignUpSerializer(data=data)
            else:
                data = UserSignUpSerializer(data=data)

            if data.is_valid(raise_exception=True):
                try:
                    fcm = data.validated_data.pop("fcm")
                except:
                    pass
                usr = data.save()
                usr.is_active = True
                usr.is_verified = True
                usr.auth_type = "GOOGLE" if serializer.validated_data['platform'] == "Google" else 'APPLE'
                usr.save()
                refresh = RefreshToken.for_user(usr)
                serialize = UserSerializer(usr)
                if fcm:
                    SignIn.handle_fcm_token(user=usr, fcm_data=fcm, request=request)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_info': serialize.data
                })


class IdentityVerificationView(APIView):
    def get(self, request, *args, **kwargs):
        if IdentityVerification.objects.filter(user=request.user).exists() is False:
            return Response(
                data={
                    "detail": "You have not submitted your document. Please upload it for verification."
                }
            )
        settings = ProjectSettings.objects.first()
        if not settings:
            return Response(
                data={
                    "detail": "Admin has not set verification prices yet."
                }
            )
        verification_obj = IdentityVerification.objects.filter(user=request.user).latest("created_at")
        serialize = IdentityVerificationSerializer(verification_obj)
        is_paid, payment_response = True, {}
        if verification_obj.status in ["expiring", "expired"] or VerificationTransaction.objects.filter(
                user=request.user, status="succeeded").exists() is False:

            check_transaction = VerificationTransaction.objects.filter(user=request.user, verification=verification_obj).order_by('-created_at').first()
            if check_transaction:
                amount = check_transaction.amount
                discount_obj = verification_obj.discount
            else:
                amount = settings.player_verification if request.user.user_role == "player" else settings.coach_verification
                discount_obj = None

            payment_response = verification_paypal_checkout_session(
                # settings.player_verification if request.user.user_role == "player" else settings.coach_verification,
                # 14.99 if request.user.user_role == "player" else 14.99,
                amount,
                user=self.request.user,
                verification_obj=verification_obj,
                discount=discount_obj
            )
            is_paid = False

        if verification_obj.status == "accept" and is_paid:
            message = "Your Submission has been approve"

        elif verification_obj.status == "reject":
            message = "Your document has been rejected. Please re-upload it."

        elif is_paid is False:
            message = "Unfortunately, your payment was declined, and we did not receive the amount. Please try again or choose a different payment method."

        elif verification_obj.status == "pending":
            message = "Your document is under review"

        elif verification_obj.status == "expired":
            message = "Your verification has expired"

        elif verification_obj.status == "expiring":
            message = "Your verification has expired in three days"
        else:
            message = "Something went wrong"

        return Response({
            "detail": message,
            "is_verified": verification_obj.status,
            "is_paid": is_paid,
            "parent_verified": verification_obj.parent_verified,
            "payment": payment_response,
            "data": serialize.data
        })

    def post(self, request, *args, **kwargs):
        data = IdentityVerificationSerializer(data=request.data, context={"user_type": request.user.user_role})
        settings = ProjectSettings.objects.first()

        if data.is_valid(raise_exception=True):
            verification_obj = IdentityVerification.objects.filter(user=request.user).first()
            if verification_obj:
                if verification_obj.status == "reject" or verification_obj.status == "pending":
                    is_paid, payment_response = True, {}
                    verification_obj = data.save(user=request.user)
                    if VerificationTransaction.objects.filter(user=request.user, status="succeeded").exists() is False:
                        amount, discount_obj = get_discounted_amount_value(
                            settings.player_verification if request.user.user_role == "player" else settings.coach_verification, request
                        )
                        payment_response = verification_paypal_checkout_session(
                            amount,
                            user=self.request.user,
                            verification_obj=verification_obj,
                            discount = discount_obj
                        )
                        is_paid = False

                    return Response({
                        "detail": "Verification has been resubmitted successfully.",
                        "is_verified": verification_obj.status,
                        "is_paid": is_paid,
                        "price": settings.player_verification if request.user.user_role == "player" else settings.coach_verification,
                        "parent_verified": verification_obj.parent_verified,
                        "payment": payment_response,
                    })

                if verification_obj.status == "accept" or request.user.is_identity_verified is True:
                    return Response({
                        "detail": "Your account is already verified."
                    }, status=status.HTTP_400_BAD_REQUEST)

            verification_obj = data.save(user=request.user, is_active=False)

            amount, discount_obj = get_discounted_amount_value(
                settings.player_verification if request.user.user_role == "player" else settings.coach_verification, request
            )
            payment_response = verification_paypal_checkout_session(
                amount,
                user=self.request.user,
                verification_obj=verification_obj,
                discount=discount_obj
            )
            send_parent_verification_mail(verification_obj)
            return Response(payment_response)


# class IdentityVerificationView(APIView):
#     def get(self, request, *args, **kwargs):
#         if IdentityVerification.objects.filter(user=request.user).exists() is False:
#             return Response(
#                 data={
#                     "detail": "You have not submitted your document. Please upload it for verification."
#                 }
#             )
#
#         settings = ProjectSettings.objects.first()
#         if not settings:
#             return Response(
#                 data={
#                     "detail": "Admin has not set verification prices yet."
#                 }
#             )
#
#         verification_obj = IdentityVerification.objects.filter(user=request.user).latest("created_at")
#         serialize = IdentityVerificationSerializer(verification_obj)
#         is_paid, payment_response = True, {}
#
#         message = VERIFICATION_STATUS_MESSAGES.get(verification_obj.status, "Your Submission has been approve")
#
#         if not VerificationTransaction.objects.filter(user=request.user, status="succeeded").exists():
#             payment_response = verification_paypal_checkout_session(
#                 settings.player_verification if request.user.user_role == "player" else settings.coach_verification,
#                 user=self.request.user,
#                 verification_obj=verification_obj
#             )
#             is_paid = False
#
#         # if is_paid is False :
#         #     message = "Unfortunately, your payment was declined, and we did not receive the amount. Please try again or choose a different payment method."
#
#         return Response({
#             "detail": message,
#             "is_verified": verification_obj.status,
#             "is_paid": is_paid,
#             "parent_verified": verification_obj.parent_verified,
#             "payment": payment_response,
#             "data": serialize.data
#         })
#
#     def post(self, request, *args, **kwargs):
#         data = IdentityVerificationSerializer(data=request.data, context={"user_type": request.user.user_role})
#         settings = ProjectSettings.objects.first()
#         if data.is_valid(raise_exception=True):
#             verification_obj = IdentityVerification.objects.filter(user=request.user).first()
#             if verification_obj:
#                 if verification_obj.status == "reject" or verification_obj.status == "pending":
#                     is_paid, payment_response = True, {}
#                     verification_obj = data.save(user=request.user)
#                     if VerificationTransaction.objects.filter(user=request.user, status="succeeded").exists() is False:
#                         payment_response = verification_paypal_checkout_session(
#                             settings.player_verification if request.user.user_role == "player" else settings.coach_verification,
#                             user=self.request.user,
#                             verification_obj=verification_obj
#                         )
#                         is_paid = False
#
#                     return Response({
#                                         "detail": "Verification has been resubmitted successfully.",
#                                         "is_verified": verification_obj.status,
#                                         "is_paid": is_paid,
#                                         "parent_verified": verification_obj.parent_verified,
#                                         "price": settings.player_verification if request.user.user_role == "player" else settings.coach_verification,
#                                         "payment": payment_response
#                                     } | payment_response)
#
#                 if verification_obj.status == "accept" or request.user.is_identity_verified is True:
#                     return Response({
#                         "detail": "Your account is already verified."
#                     }, status=status.HTTP_400_BAD_REQUEST)
#
#             verification_obj = data.save(user=request.user, is_active=False)
#
#             payment_response = verification_paypal_checkout_session(
#                 settings.player_verification if request.user.user_role == "player" else settings.coach_verification,
#                 user=self.request.user,
#                 verification_obj=verification_obj
#             )
#
#             # send_parent_verification_mail(verification_obj)
#             payment_response[
#                 'price'] = settings.player_verification if request.user.user_role == "player" else settings.coach_verification
#             payment_response['is_paid'] = True
#             return Response(payment_response)


class AthleteTypesView(generics.ListAPIView):
    serializer_class = AthleteTypeSerializer
    queryset = AthleteTypes.objects.all()
    permission_classes = [AllowAny]


class DocumentTypesView(generics.ListAPIView):
    serializer_class = DocumentTypeSerializer
    queryset = DocumentType.objects.all()
    permission_classes = [AllowAny]


class ResendParentConsent(APIView):
    serializer_class = ResendParentConsent

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            verification_obj = serializer.validated_data['verification']
            if verification_obj.user.id != request.user.id:
                return Response({
                    "detail": "Something went wrong we could not identify your verification. please try again."
                }, status=status.HTTP_400_BAD_REQUEST)

            verification_obj.parent_email = serializer.validated_data.get("parent_email", verification_obj.parent_email)
            verification_obj.parent_legal_name = serializer.validated_data.get("parent_legal_name",
                                                                               verification_obj.parent_legal_name)
            verification_obj.parent_phone_number = serializer.validated_data.get("parent_phone_number",
                                                                                 verification_obj.parent_phone_number)
            verification_obj.save()

            send_parent_verification_mail(verification_obj)
            return Response({"detail": f"Parent consent send successfully to {verification_obj.parent_email}."})


class ReferralOrganizationView(generics.ListAPIView):
    queryset = ReferralOrganization.objects.filter(is_active=True)
    serializer_class = ReferralOrganizationSerializer


class SchoolDocumentView(generics.ListAPIView):
    queryset = SchoolDocument.objects.filter(is_active=True)
    serializer_class = SchoolDocumentSerializer
    permission_classes = [AllowAny]


class ValidateDiscountCodeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ValidateDiscountCodeSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response({"detail": serializer.errors["discount_code"][0]},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"detail": "Discount code validated successfully"}, status=status.HTTP_200_OK)
# class ApplyDiscountCodeAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         serializer = ApplyDiscountSerializer(
#             data=request.data,
#             context={"request": request}
#         )
#
#         serializer.is_valid(raise_exception=True)
#         discount = serializer.validated_data["discount"]
#         user = request.user
#
#         discount.users.add(user)
#         discount.used_count += 1
#
#         if discount.used_count >= discount.usage_limit:
#             discount.is_active = False
#
#         discount.save(update_fields=["used_count", "is_active"])
#
#         return Response(
#             {"detail": "Discount code applied successfully."},
#             status=status.HTTP_200_OK
#         )


# class GetMyDiscountCodeView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         discount = DiscountCode.objects.filter(
#             owner=request.user,
#             is_deleted=False
#         ).first()
#
#         if not discount:
#             return Response(
#                 {"detail": "No discount code found for you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#
#         serializer = DiscountCodeSerializer(discount)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     def post(self, request):
#         if DiscountCode.objects.filter(owner=request.user, is_deleted=False).exists():
#             return Response(
#                 {"detail": "You can create a discount code only once."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         usage_limit = request.data.get("usage_limit")
#         discount = DiscountCode.objects.create(
#             owner=request.user,
#             usage_limit=usage_limit if usage_limit else 0
#         )
#         serializer = DiscountCodeSerializer(discount)
#         return Response(
#             {
#                 "detail": "Discount code created successfully.",
#                 **serializer.data
#             },
#             status=status.HTTP_201_CREATED
#         )
