from django.urls import path
from . import views


urlpatterns = [
    path("", views.view_all_fans_list, name="fans_management"),
    path("<pk>/", views.view_fan_profile, name="fan_profile")

]

