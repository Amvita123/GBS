from django.urls import path
from .import views

urlpatterns = [
    path("action/<str:pk>/", views.EventAPIView.as_view(), name="event-detail"),
    path("", views.EventAPIView.as_view()),
    path("follow/", views.EventFollow.as_view(), name='event_follow'),
    path("coach/", views.CoachEvent.as_view(), name="coach_self_events"),
    path("types/", views.EventTypes.as_view(), name="event_types"),
    path("check-in/<event_id>/", views.EventCheckInRosterUser.as_view()),
    path("check-in/", views.EventCheckInView.as_view(), name="event_checkin"),
    path("plans/", views.EventPlanView.as_view(), name="event_plans"),
    path("payment/webhook/", views.PaymentWebhook.as_view(), name="web_hook"),
    path("repay/<id>/", views.EventRepayment.as_view()),
    path("team/<id>/", views.EventTeam.as_view()),
    path("leaderboard/<event_id>/", views.EventLeaderBoard.as_view()),
    path("payment/success/", views.paypal_capture_payment),
    path("submit-roster/", views.RosterSubmission.as_view()),

]
