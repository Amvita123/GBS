from django.urls import path, include
from . import views

urlpatterns = [
    path("login/", views.user_login, name="login"),
    path('change-password/', views.change_password, name='change_password'),
    path("", views.dashboard, name="dashboard"),
    path("logout/", views.user_logout, name="logout"),
    path("profile/", views.user_profile, name="profile"),
    path("subscription/", views.subscription, name="subscription"),
    path("post-report/", include([
        path("", views.view_all_post_reports, name="post_report_management"),
        path("<pk>/details/", views.view_report_post, name="post_report_details")
    ])),
    path("content-management/", views.content_management, name="content_management"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-condition/", views.terms_condition, name="terms_condition"),
    path("support/", views.support_page, name="support_page"),
    path('stream-video/', views.stream_video, name='stream_video'),
    path("app/<action>/<mobile_os>/", views.redirect_on_store, name="redirect_on_store"),
    path("settings/", views.project_settings, name="settings"),
    path('add-sport/', views.add_sport, name='add_sport'),
    path("<pk>/details/", views.sport_details, name="sport_details"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-forgot-otp/', views.verify_forgot_otp, name='verify_forgot_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),

    path('discount-management/', views.discount_management, name='discount_management'),
    path('create-discount-code/', views.create_discount_code, name='create_discount_code'),
    path('edit-discount-code/<uuid:pk>/', views.edit_discount_code, name='edit_discount_code'),
    path('usage-report/<uuid:pk>/', views.usage_report, name='usage_report'),

]

