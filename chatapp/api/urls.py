from django.urls import path
from .import views


urlpatterns = [
  path("group/", views.PlayerChallengeGroup.as_view()),
  path("<int:challenge_id>/", views.ChallengeChatView.as_view()),
  path("connection/", views.UserConnectionsView.as_view()),


]

