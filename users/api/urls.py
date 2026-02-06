from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("sign-up/", views.UserSignUp.as_view(), name="users_sign_up"),
    path("verify-otp/", views.OtpVerification.as_view(), name="otp_verification"),
    path('sign-in/', views.SignIn.as_view(), name='token_obtain_pair'),
    path("sign-out/", views.SignOut.as_view(), name="user_sign_out"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("profile/", views.UserProfile.as_view(), name="UserProfile"),
    path("change-password/", views.ChangePassword.as_view(), name="ChangePassword"),
    path("forget-password/", views.RequestForgetPassword, name="request_forget_password"),
    path("verify-forget-otp/", views.ValidateForgetPasswordOTP, name="forget_otp_verify"),
    path("reset-password/", views.ResetPassword, name="reset_password"),
    path("follow/<str:action>/", views.UserFollow.as_view(), name="follower_get"),
    path("follow/", views.UserFollow.as_view(), name="follower_following"),
    path("block/", views.BlockUserView.as_view(), name="user_blocking"),
    path("social-sign-in/", views.SocialLogin.as_view(), name="social_login"),
    path("identity-verification/", views.IdentityVerificationView.as_view()),
    path("athlete-type/", views.AthleteTypesView.as_view()),
    path("document-type/", views.DocumentTypesView.as_view()),
    path("send-parent-consent/", views.ResendParentConsent.as_view()),
    path("referral-organization/", views.ReferralOrganizationView.as_view()),
    path("school-docs/", views.SchoolDocumentView.as_view()),  # test

    path("validate-code/", views.ValidateDiscountCodeAPIView.as_view(), name="validate_discount_code")
]
