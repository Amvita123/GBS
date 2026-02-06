from django.urls import path
from .import views

urlpatterns = [
    path("terms-condition/", views.TermsConditionAPIView.as_view()),
    path("settings/", views.ProjectSettingsAPIView.as_view()),

]
