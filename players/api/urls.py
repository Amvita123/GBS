from django.urls import path
from . import views

urlpatterns = [
    path("post/", views.Post_Feed.as_view(), name="post_feed"),
    path("post/<uuid:feed_id>/", views.Post_Feed.as_view(), name="post_feed"),
    path("squad/", views.SquadView.as_view(), name="squad"),
    path("post-rating/", views.FeedSkillsRatingView.as_view(), name="FeedSkillsRating"),
    path("badges/", views.BadgeList.as_view(), name="badges"),
    path("skills/", views.SkillList.as_view(), name="skills"),
    path("challenge/", views.ChallengeView.as_view(), name="challenge"),
    path("challenge/action/", views.ChallengeAction.as_view(), name="challenge_action"),
    path("position/", views.Positions.as_view(), name="player_position"),
    path("playing-style/<int:pk>/", views.PositionPlayingStyle.as_view(), name="position_playing_style"),
    path("squad-structure/", views.SquadStructureView.as_view(), name="SquadStructureView"),
    path("sport/", views.AllSports.as_view(), name="all_sports_list"),
    path("squad-leaderboard/", views.SquadLeaderboard.as_view(), name="squad_leaderboard"),
    path("grade/", views.SchoolGradeView.as_view()),
    path("roster/", views.PlayerRoster.as_view()),
    path("roster-exit/", views.RosterExitRequestView.as_view()),


]

