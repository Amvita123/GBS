from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from notification.task import send_user_action_notification


class DashboardFeedPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "results": data
        })


def send_feed_notification(request, feed, action):
    if request.user.username == feed.user.username:
        return
    notification_obj = {
        "action": "user_profile", "sender": request.user.username,
        "receiver": feed.user.username, "object_id": str(feed.id)
    }

    match action:
        case "dislike":
            notification_obj['message'] = f'{request.user.username.title()} removed their like from your post.'
        case "like":
            notification_obj['message'] = f'{request.user.username.title()} liked your post.'
        case "comment":
            notification_obj['message'] = f'{request.user.username.title()} comment on your post.'
        case "report":
            notification_obj['message'] = f'{request.user.username.title()} report on your post.'
        case _:
            notification_obj['message'] = ""

    send_user_action_notification.delay(
        **notification_obj
    )

