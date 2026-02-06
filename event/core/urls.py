from django.urls import path
from . import views

urlpatterns = [
    path("", views.view_all_events, name="event_management"),
    path("edit/<pk>/", views.edit_event, name="event_edit"),
    path("create/", views.create_new_event, name="create_event"),
    path("<pk>/details/", views.event_details, name="event_detail"),
    path("plans/", views.event_plan_management, name="event_plan"),
    path("check-in/<pk>/users/", views.event_check_in_users, name="event_check_in_users"),
    path("payment/<str:action>/", views.event_payment_callback, name="event_payment_callback"),
    path("transaction/", views.transaction_management, name="transaction_management"),
    path("upload/<pk>/event-check-in/", views.upload_event_check_in_csv, name="insert_event_check_in_csv"),
    path("insert/<pk>/event-check-in/", views.insert_event_check_in_csv, name="event_check_csv_data"),
    path("event/<uuid:pk>/assign-sub-admin/", views.assign_sub_admin, name="assign_sub_admin"),
    path("duplicate/<pk>/", views.duplicate_event, name="event_duplicate"),


]

