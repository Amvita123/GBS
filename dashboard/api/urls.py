from django.urls import path, include
from . import views
import uuid

urlpatterns = [
    path("feed/", include([
        path("like/", views.FeedLike.as_view(), name="feed_like"),
        path("comment/", views.FeedComment.as_view(), name="feed_comment"),
        path("<uuid:feed_pk>/comment/", views.FeedComment.as_view(), name="feed_comment"),
        path("report/", views.FeedReportView.as_view(), name="feed_report"),
        path("report-reason/", views.FeedReportReason.as_view()),
        path("share/", views.FeedShare.as_view()),

    ]), name="feed_routes"),
    path("post/", views.DashboardFeed.as_view()),
    path("post/<str:pk>/", views.DashboardFeed.as_view()),
    path('my-post/', views.MyFeed.as_view()),
]

