from django.urls import path
from .import views

urlpatterns = [
    path("", views.NotificationView.as_view()),

]
