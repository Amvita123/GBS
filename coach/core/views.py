from django.shortcuts import redirect, render
from users.models import User
from django.core.paginator import Paginator
from .utils import users_management_actions as coach_management_actions
from django.urls import reverse
from common.models import Feed
from django.db.models import Q
from players.models import Follow
from django.contrib import messages
from common.services import admin_required, sub_admin_required
from .form import CoachTypeForm, CoachType, RosterGradeForm
from coach.models import Organization, OrganizationTransaction, Roster, RosterGrade
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from django.views.decorators.http import require_http_methods


@sub_admin_required
def view_all_coach(request):
    if request.method == "POST":
        form = CoachTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"{form.cleaned_data.get('name')} has been created successfully.")
            return redirect('coach_management')
        else:
            form_error = True

    coaches = User.objects.filter(user_role="coach").order_by("-date_joined")
    query = request.GET.get("q")
    if request.user.user_role == "sub_admin" and not query:
        return render(request, "athletes/search_athlete.html", {"page_title": "Coach Management", "key": "coach"})

    if query:
        filters = Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(
            last_name__icontains=query)
        query = query.replace(" ", "")

        coaches = coaches.filter(filters)

    coach_types = CoachType.objects.all()
    page_number = request.GET.get("page", 1)

    if request.GET.get("from") and request.GET.get("to"):
        coaches = coaches.filter(date_joined__date__range=[request.GET.get("from"), request.GET.get("to")])

    if coach_management_actions(request, coaches):
        return redirect(f"{reverse('coach_management')}?page={page_number}{f'&q={query}' if query else ''}")

    paginator = Paginator(coaches, 100)
    coaches = paginator.get_page(page_number)
    page_coach = True
    return render(request, "coach/view_all.html", locals())


@sub_admin_required
def view_profile(request, pk):
    coach = User.objects.filter(user_role="coach", id=pk).first()
    if request.GET.get("action") == "delete_post":
        Feed.objects.filter(id=request.GET.get("id"), user=coach).delete()
        messages.success(request, "post has been deleted successfully.")
        return redirect("coach_profile", pk)

    posts = Feed.objects.select_related("user").filter(user=coach).order_by('-created_at')[:3]
    user_follow = Follow.objects.select_related("follower", "following").filter(Q(follower=coach) | Q(following=coach))
    followers = user_follow.filter(following=coach)
    following = user_follow.filter(follower=coach)

    followers_paginator = Paginator(followers, 25)
    followers_page_number = request.GET.get("follower-page")
    followers = followers_paginator.get_page(followers_page_number)

    following_paginator = Paginator(following, 25)
    following_page_number = request.GET.get("following-page", 1)
    following = following_paginator.get_page(following_page_number)
    page_coach = True
    return render(request, "coach/profile.html", locals())


@admin_required
def organization_management(request):
    organizations = Organization.objects.filter(is_active=True)
    page_number = request.GET.get("page", 1)
    page_org = True
    paginator = Paginator(organizations, 100)
    organizations = paginator.get_page(page_number)
    return render(request, "coach/organization.html", locals())


@admin_required
def organization_detail(request, pk):
    organization = get_object_or_404(Organization, id=pk)
    page_org = True
    return render(request, "coach/organization_detail.html", locals())


@admin_required
def organization_transaction_detail(request, pk):
    organization_transaction = OrganizationTransaction.objects.select_related("organization").filter(
        organization__id=pk).order_by("-created_at")
    page_org = True
    return render(request, "coach/organization_transaction.html", locals())


@admin_required
def roster_detail(request, pk):
    if request.method == "POST":
        print(request.POST)

    roster = get_object_or_404(Roster, id=pk)
    page_org = True
    players = User.objects.filter(is_active=True)
    return render(request, "coach/roster_details.html", locals())


def download_roster_detail_pdf(request, pk):
    roster = get_object_or_404(Roster, pk=pk)
    html = render_to_string("coach/roster_pdf.html", {"roster": roster, "request": request})

    pdf = weasyprint.HTML(string=html).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=roster_{pk}.pdf"
    return response


@admin_required
def roster_grade(request):
    if request.method == "POST":
        form = RosterGradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade has been added successfully.")
        else:
            messages.error(request, "Unable to add grade. Please try again.")
            open_add_modal = True
        return redirect("roster_grade")

    grades = RosterGrade.objects.all()

    if request.GET.get("action") == "delete":
        try:
            grade = grades.filter(id=request.GET.get("id")).first()
            grade.delete()
            messages.success(request, "Grade has been deleted successfully.")
            return redirect("roster_grade")
        except Exception as e:
            print(e)
            messages.error(request, "Unable to delete grade. Please try again.")

    return render(request, "coach/grade.html", locals())


@admin_required
def edit_roster_grade(request):
    if request.method == "POST":
        pk = request.POST['id']
        roster = get_object_or_404(RosterGrade, id=pk)
        grade_id = pk
        form = RosterGradeForm(request.POST, instance=roster)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade has been updated successfully.")
        else:
            edit_model_open = True
            form_name = request.POST.get("name")
            messages.error(request, "Unable to updated grade. Please try again.")
            grades = RosterGrade.objects.all()
            return render(request, "coach/grade.html", locals())

    return redirect("roster_grade")


@admin_required
@require_http_methods(["GET"])
def load_players_html(request):
    roster_id = request.GET.get('roster_id')
    search_query = request.GET.get('search', '').strip()
    players = User.objects.filter(
        user_role="player",
        is_identity_verified=True
    ).exclude(
        rosterplayer__roster_id=roster_id
    )

    if search_query:
        players = players.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(verification__legal_full_name__icontains=search_query)
        )

    players = players.distinct()

    return render(request, 'partials/players_list.html', {'players': players})


@admin_required()
@require_http_methods(["GET"])
def load_coaches_html(request):
    roster_id = request.GET.get('roster_id')
    search_query = request.GET.get('search', '').strip()
    players = User.objects.filter(
        user_role="coach",
        is_identity_verified=True
    ).exclude(
        rostercoach__roster_id=roster_id
    )

    if search_query:
        players = players.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(verification__legal_full_name__icontains=search_query)
        )

    coaches = players.distinct()

    return render(request, 'partials/coaches_list.html', {'coaches': coaches})



