from django.shortcuts import render, redirect, get_object_or_404
from common.services import admin_required, sub_admin_required
from users.models import User, IdentityVerification
from django.contrib import messages
from django.core.paginator import Paginator
from players.models import Squad, Follow, Badge, Challenge, PlayerBadges, BadgeLevel, Player, TemplateCache, SchoolGrade
from common.models import Feed
from django.db.models import Q
from .forms import JerseyNumberForm, BadgeForm, GradeForm
from django.urls import reverse
from .utils import athlete_profile_action
from coach.core.utils import users_management_actions
from django.db import IntegrityError
from notification.task import send_single_user_admin_notification
from openpyxl import Workbook
from django.http import HttpResponse
from players.task import cal_overall_rating


@sub_admin_required
def view_all_athletes(request):
    # save grade
    if request.method == "POST":
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"{form.cleaned_data.get('name')} grade has been created successfully.")
            return redirect("athlete_management")
        else:
            form_error = True

    athletes = User.objects.filter(user_role="player").order_by("-date_joined")
    query = request.GET.get("q")
    if request.user.user_role == "sub_admin" and not query:
        return render(request, "athletes/search_athlete.html", {"page_title": "Athlete Management", "key": "athlete"})

    if query:
        filters = Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(
            last_name__icontains=query)
        query = query.replace(" ", "")
        if query.isdigit():
            filters |= Q(player__jersey_number=int(query))

        athletes = athletes.filter(filters)
    elif request.GET.get("from") and request.GET.get("to"):
        athletes = athletes.filter(date_joined__date__range=[request.GET.get("from"), request.GET.get("to")])

    user_id = request.GET.get("id")
    page_number = request.GET.get("page")

    if users_management_actions(request, athletes):
        return redirect(f"{reverse('athlete_management')}?page={page_number}{f'&q={query}' if query else ''}")

    paginator = Paginator(athletes, 100)
    athletes = paginator.get_page(page_number)
    athlete_grades = SchoolGrade.objects.all()

    return render(request, "athletes/view_all.html", locals())


@sub_admin_required
def athlete_profile(request, pk):
    athlete = User.objects.filter(user_role="player", id=pk).first()
    earned_badges = athlete.badge.all().order_by('created_at')
    badges = Badge.objects.all().order_by("is_admin_assignable")

    if athlete_profile_action(request):
        return redirect("athlete_profile", pk)

    if request.method == "POST":
        if "jerseyNumber" in request.POST:
            jersey_form = JerseyNumberForm(request.POST)
            if jersey_form.is_valid():
                profile = athlete.player_profile
                profile.jersey_number = jersey_form.cleaned_data['jersey_number']
                profile.save()
                messages.success(request, f"Jersey Number {profile.jersey_number} assigned to {athlete.username}.")
                return redirect("athlete_profile", pk)
            else:
                jersey_player = Player.objects.filter(jersey_number=request.POST.get("jersey_number")).first()

        elif "AssignBadge" in request.POST:
            templates = request.POST.getlist('template')
            non_template_badge = request.POST.getlist('non_template_badge')

            select_badges = {}
            for i in templates:
                badge = i.split("_")
                if badge[0] in select_badges:
                    select_badges[badge[0]].append(badge[1])
                else:
                    select_badges[badge[0]] = [badge[1]]

            earned_badges.delete()

            for badge_id, template in select_badges.items():
                template_count = len(template)
                badge = badges.filter(id=badge_id).first()

                if 4 <= template_count <= 7:
                    badge_level = "bronze"

                elif 8 <= template_count <= 12:
                    badge_level = "silver"

                elif template_count > 12:
                    badge_level = "gold"

                else:
                    badge_level = None
                    TemplateCache.objects.create(
                        badge=badge,
                        user=athlete,
                        templates=template
                    )

                if badge_level:
                    badge_level = BadgeLevel.objects.select_related('badge').filter(
                        name=badge_level,
                        badge__id=badge_id
                    ).first()

                    player_badge = PlayerBadges(
                        user=athlete,
                        badge=badge,
                        templates=template,
                        assigned_by=request.user
                    )
                    player_badge.badge_level = badge_level
                    player_badge.save()

            # non template badge
            player_badges_to_create = []
            for badge_in in non_template_badge:
                badge = badges.filter(id=badge_in).first()
                if badge:
                    player_badges_to_create.append(
                        PlayerBadges(
                            user=athlete,
                            badge=badge,
                            assigned_by=request.user
                        )
                    )

            PlayerBadges.objects.bulk_create(player_badges_to_create)
            send_single_user_admin_notification.delay(
                username=athlete.username,
                user_id=athlete.id,
                message=f"Hello {athlete.username}! badge has been updated. Check your profile to see your latest achievement.",
                title="Badge Earned Update! 🏅"
            )
            try:
                cal_overall_rating(athlete.id)
            except Exception as e:
                print(e)
            messages.success(request, f"Badge assigned to {athlete.username} successfully.")
            # return redirect("athlete_profile", pk)
            return redirect(f"/athlete/{pk}/")

    squads = Squad.objects.select_related("created_by").prefetch_related("players").filter(
        Q(created_by=athlete) |
        Q(players=athlete)
    ).distinct()

    number_of_squads = squads.count()
    squad = squads.filter(created_by=athlete).first()
    posts = Feed.objects.select_related("user").filter(user=athlete).order_by('-created_at')[:3]
    user_follow = Follow.objects.select_related("follower", "following").filter(
        Q(follower=athlete) | Q(following=athlete))
    followers = user_follow.filter(following=athlete)
    following = user_follow.filter(follower=athlete)

    followers_paginator = Paginator(followers, 25)
    followers_page_number = request.GET.get("follower-page")
    followers = followers_paginator.get_page(followers_page_number)

    following_paginator = Paginator(following, 25)
    following_page_number = request.GET.get("following-page")
    following = following_paginator.get_page(following_page_number)

    # badge_levels = ["bronze", "silver", "gold"]

    assigned_badge_template = []
    assigned_badge_list = []
    for i in earned_badges:
        if i.templates:
            assigned_badge_template += [f'{i.badge.id}{j}'.replace(" ", '').lower() for j in i.templates]
        if i.badge_level:
            assigned_badge_list.append(f'{i.badge.id}_{i.badge_level.name}')
        else:
            assigned_badge_list.append(f'{i.badge.id}')

    for i in TemplateCache.objects.filter(user=athlete):
        assigned_badge_template += [f'{i.badge.id}{j}'.replace(" ", '').lower() for j in i.templates]

    verification_obj = IdentityVerification.objects.select_related("user").filter(
        user=athlete
    ).first()

    return render(
        request,
        "athletes/profile.html",
        locals()
    )


@admin_required
def export_athletes_csv(request):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Athletes'

    headers = ['FirstName', 'LastName', 'Email', 'Username', 'Position', "Playing Style", 'Badges Earned', 'JerseyNo']
    worksheet.append(headers)

    for athlete in User.objects.filter(user_role="player").order_by("first_name"):
        worksheet.append([
            athlete.first_name,
            athlete.last_name,
            athlete.email,
            athlete.username,
            athlete.player_profile.position.name,
            athlete.player_profile.playing_style.title,
            athlete.badge.all().count() if athlete.badge else 0,
            athlete.player_profile.jersey_number,
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=athletes.xlsx'
    workbook.save(response)
    return response


@admin_required
def view_all_challenge_list(request):
    challenges = Challenge.objects.all()
    page_number = request.GET.get("page")
    challenges = Paginator(challenges, 25).get_page(page_number)
    return render(request, "athletes/view_all_challenge.html", locals())


@admin_required
def challenge_details(request, pk):
    challenge = Challenge.objects.get(id=pk)
    return render(request, "athletes/view_challenge_details.html", locals())


@admin_required
def view_all_badges_list(request):
    badges = Badge.objects.all()
    if request.method == "POST":
        badge = badges.get(id=request.POST['id'])
        form = BadgeForm(request.POST, instance=badge)
        if form.is_valid():
            form.save()
            messages.success(request, f"{badge.name} updated successfully.")
            return redirect("badges_management")
    elif request.GET.get("action") == "delete":
        badge = badges.get(id=request.GET.get('id'))
        messages.success(request, f"{badge.name} deleted successfully.")
        badge.delete()
        return redirect("badges_management")
    return render(request, "athletes/view_all_badges.html", locals())




