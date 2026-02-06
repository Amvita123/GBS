from django.urls import path, re_path
from . import consumers

ws_urlpatterns = [
    re_path(r"ws/chat/(?P<challenge_id>\w+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"^ws/single-chat/(?P<user_id>[\w-]+)/$", consumers.PersonalChat.as_asgi())
]


