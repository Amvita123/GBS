from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import InvalidSignatureError, ExpiredSignatureError, DecodeError
from jwt import decode as jwt_decode

User = get_user_model()


class JWTAuthMiddleware:
    """Middleware to authenticate user for channels"""

    def __init__(self, app):
        """Initializing the app."""
        self.app = app

    async def __call__(self, scope, receive, send):
        """Authenticate the user based on JWT."""
        close_old_connections()
        try:
            # Decode the query string and get token parameter from it.
            query_params = parse_qs(scope["query_string"].decode("utf8"))
            token = query_params.get("token")

            if not token:
                raise ValueError("Token is required for authentication.")

            token = token[0]  # Extract token value from the list

            data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            # Get the user from database based on user id and add it to the scope.
            user = await self.get_user(data["user_id"])

            if isinstance(user, AnonymousUser):
                raise ValueError("Invalid token. Authentication failed.")

            # if user.user_role != "player":
            #     raise ValueError("Invalid token. Authentication failed.")

            scope["user"] = user

        except (ValueError, TypeError, KeyError, InvalidSignatureError, ExpiredSignatureError, DecodeError) as e:
            # Raise an exception instead of setting user as AnonymousUser
            await send({
                "type": "websocket.close",
                "code": 401,
                "reason": str(e),
            })
            return

        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        """Return the user based on user ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()


def JWTAuthMiddlewareStack(app):
    """Wrap channels authentication stack with JWTAuthMiddleware."""
    return JWTAuthMiddleware(AuthMiddlewareStack(app))
