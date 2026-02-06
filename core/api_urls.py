from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


schema_view = get_schema_view(
    openapi.Info(
        title="Youth Basketball Player, Parent & Fan ",
        default_version="v1",
        description="",
        # terms_of_service="https://example.com/terms/",
        contact=openapi.Contact(email="mohan.pandit@cssoftsolutions.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[AllowAny],
    authentication_classes=[JWTAuthentication]
)

urlpatterns = [
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("users/", include("users.api.urls")),
    path("players/", include("players.api.urls")),
    path("", include("dashboard.api.urls")),
    path("notification/", include("notification.api.urls")),
    path("chat/", include("chatapp.api.urls")),
    path("event/", include("event.api.urls")),
    path("", include("common.api.urls")),
    path("coach/", include("coach.api.urls"))
]
