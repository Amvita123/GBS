from django.urls import path
from . import views


urlpatterns = [
    path("", views.view_all_coach, name="coach_management"),
    path("<pk>/", views.view_profile, name="coach_profile"),
    path("organization-management", views.organization_management, name="organization_management"),
    path("organization-detail/<pk>/", views.organization_detail, name="organization_detail"),
    path("organization-transaction/<pk>/", views.organization_transaction_detail, name="organization_transaction_detail"),
    path("roster/<pk>/detail/", views.roster_detail, name="roster_detail"),
    path("roster/grade/", views.roster_grade, name="roster_grade"),
    path("roster/grade/update/", views.edit_roster_grade, name="edit_roster_grade"),
    path("roster/<pk>/pdf/", views.download_roster_detail_pdf, name="download_roster_pdf"),
    path('roster/load-players-html/', views.load_players_html, name='load_players_html'),
    path('roster/load-coaches-html/', views.load_coaches_html, name='load_coaches_html'),

]



