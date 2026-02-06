from django.urls import path, include
from . import views

urlpatterns = [
   path("athlete/", include([
       path("", views.view_all_athletes, name="athlete_management"),
       path("export/", views.export_athletes_csv, name="export_athletes_csv"),
       path("<pk>/", views.athlete_profile, name="athlete_profile"),
   ])),

   path("challenge/", include([
       path("", views.view_all_challenge_list, name="challenge_management"),
       path("<pk>/", views.challenge_details, name="challenge_details"),
   ])),

   path("badges/", include([
       path("", views.view_all_badges_list, name="badges_management"),

   ]))

]

