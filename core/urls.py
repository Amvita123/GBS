from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from core import settings
from .api_urls import urlpatterns as api_urls
from dashboard.api.views import AndroidDeeplink, IosDeeplink

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(api_urls)),
    path("", include("dashboard.core.urls")),
    path("", include("players.core.urls")),
    path("coach/", include("coach.core.urls")),
    path("fan/", include("fans.core.urls")),
    path("event/", include("event.core.urls")),
    path("notification/", include("notification.core.urls")),
    path("users/", include("users.core.urls")),
    path(".well-known/assetlinks.json", AndroidDeeplink, name="android_deeplink"),
    path(".well-known/apple-app-site-association", IosDeeplink, name="apple_deeplink"),

]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


