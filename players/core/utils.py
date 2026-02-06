from common.models import Feed
from django.contrib import messages
from django.shortcuts import redirect


def athlete_profile_action(request):
    if request.GET.get("action") == "delete_post":
        Feed.objects.filter(id=request.GET.get("id")).delete()
        messages.success(request, "post has been deleted successfully.")
        return True

    return False


