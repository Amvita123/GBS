from django.urls import path
from . import views


urlpatterns = [
    path("one-vs-one/", views.OneToOneSimulation.as_view()),
    path("five-vs-five/", views.FiveVsFiveSimulation.as_view()),
    path("squad/", views.SquadView.as_view(), name="get_all_squads"),
    path("five-vs-five-player/", views.FiveVsFivePlayer.as_view()),
    path("types/", views.CoachTypeView.as_view()),
    path("organization/", views.OrganizationView.as_view()),
    path("organization/all/", views.AllOrganizationView.as_view()),
    path("roster/", views.RosterView.as_view()),
    path("roster/invite/", views.InvitePlayerView.as_view()),
    path("roster-invite/", views.InviteAppPlayerView.as_view()),
    path("roster-invitation/", views.RosterInvitationActionView.as_view()),
    path("roster-grade/", views.RosterGradeView.as_view()),
    path("roster-player-jersey/", views.AssignJerseyNumber.as_view()),
    path('rosters/delete-user/', views.delete_roster_user, name='delete-roster-user'),
    path("roster-exist/", views.HandlerRosterExit.as_view()),

]

