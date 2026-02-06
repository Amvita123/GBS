from django.shortcuts import render, redirect
from common.services import admin_required, sub_admin_required
from users.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from coach.core.utils import users_management_actions
from django.urls import reverse
from common.models import Feed
from players.models import Follow
from django.db.models import Q


@sub_admin_required
def view_all_fans_list(request):
    fans = User.objects.filter(user_role="fan").order_by("-date_joined")
    if request.GET.get("from") and request.GET.get("to"):
        fans = fans.filter(date_joined__date__range=[request.GET.get("from"), request.GET.get("to")])

    query = request.GET.get("q")
    if request.user.user_role == "sub_admin" and not query:
        return render(request, "athletes/search_athlete.html", {"page_title": "Fan Management", "key": "fan"})
    if query:
        filters = Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(
            last_name__icontains=query)
        query = query.replace(" ", "")

        fans = fans.filter(filters)

    page_number = request.GET.get("page", 1)

    if users_management_actions(request, fans):
        return redirect(f"{reverse('fans_management')}?page={page_number}")

    paginator = Paginator(fans, 100)
    fans = paginator.get_page(page_number)
    return render(request, "fans/view_all.html", locals())


@sub_admin_required
def view_fan_profile(request, pk):
    fan = User.objects.filter(user_role="fan", id=pk).first()
    if request.GET.get("action") == "delete_post":
        Feed.objects.filter(id=request.GET.get("id"), user=fan).delete()
        messages.success(request, "post has been deleted successfully.")
        return redirect("coach_profile", pk)

    posts = Feed.objects.select_related("user").filter(user=fan).order_by('-created_at')[:3]
    user_follow = Follow.objects.select_related("follower", "following").filter(Q(follower=fan) | Q(following=fan))
    followers = user_follow.filter(following=fan)
    following = user_follow.filter(follower=fan)

    followers_paginator = Paginator(followers, 25)
    followers_page_number = request.GET.get("follower-page")
    followers = followers_paginator.get_page(followers_page_number)

    following_paginator = Paginator(following, 25)
    following_page_number = request.GET.get("following-page")
    following = following_paginator.get_page(following_page_number)
    return render(request, "fans/profile.html", locals())

