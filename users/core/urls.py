from django.urls import path
from . import views

urlpatterns = [
    path("sub-admin/", views.view_all_sub_admin, name="sub_admin_management"),
    path("create-sub-admin/", views.create_sub_admin, name="create_sub_admin"),
    path("sub-admin/<pk>/", views.sub_admin_profile, name="sub_admin_profile"),
    path("identity-verification/", views.identity_verification, name="identity_verification"),
    path("identity-verification/<pk>/", views.identity_detail, name="identity_verification_detail"),
    path("identity-transaction/<pk>/", views.identity_verification_transaction_detail, name="identity_verification_transaction_detail"),
    path("parent-verification/<pk>/", views.parent_verification, name="parent_verification"),
    path("resend/<pk>/password/", views.resend_password, name="resend_password"),
    path(route="referer-revenue/<referer>/", view=views.revenue_detail, name="referer_revenue_detail"),
]
