from django.urls import path
from .import views


urlpatterns = [
    path("", views.push_notification, name="send_push_notification"),
    # path("select-notification", views.select_notification, name="select_notification"),
    path("update/", views.update_upcoming_notification, name="update_notification"),
    path("<action>/", views.notification_history, name="notification_history"),

]


