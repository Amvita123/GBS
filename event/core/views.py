from django.shortcuts import redirect, render, get_object_or_404
from common.services import admin_required, sub_admin_required, require_permission
from event.models import Event, EventRules, EventPlan, EventCheckIn, EventTransaction, Team, EventTeamUser
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import EventForm, EventRuleForm, UploadCsvForm
from django.urls import reverse
from users.models import User
from django.contrib.sites.models import Site
import pandas as pd
from django.core.cache import cache
from players.models import PlayingStyle, Position, Player, Sport, SchoolGrade
from django.db.models import Q

from django.db.models import Case, When, Value, IntegerField
from django.utils import timezone

from django.utils import timezone
from datetime import timedelta



@sub_admin_required
def view_all_events(request):
    page_number = request.GET.get("page", 1)
    created_by = request.GET.get("user-id", None)
    now = timezone.now()

    if request.user.is_superuser or request.user.user_role == "ar_staff":
        events = Event.objects.select_related('user').filter(is_active=True).order_by("-created_at").annotate(
            is_upcoming=Case(
                When(
                    Q(date__gte=now) | Q(date__lte=now, end_date__gte=now),
                    then=Value(0)
                ),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('is_upcoming', 'date')
    else:
        events = Event.objects.filter(Q(user=request.user) | Q(sub_admins=request.user)).order_by("-created_at")

    if created_by:
        events = events.filter(Q(user__id=created_by) | Q(sub_admins__id=created_by)).order_by("-created_at")

    if request.GET.get("action") == "delete":
        get_object_or_404(events, id=request.GET['id']).delete()
        return redirect(f"{reverse('event_management')}?page={page_number}")
    paginator = Paginator(events, 100)
    events = paginator.get_page(page_number)
    return render(request, "event/view_all.html", locals())


@require_permission("users.edit_events")
def edit_event(request, pk):
    event = get_object_or_404(Event, id=pk)
    if request.method == "POST":
        rules = request.POST.getlist("rules", [])
        booking_links = request.POST.getlist("booking_link")
        links_label = request.POST.getlist("booking_link_label")

        try:
            booking_links = dict(zip(links_label, booking_links))
        except Exception as e:
            print(e)
            messages.error(request, f"Event create failed due to {str(e)}")
            return render(request, "event/edit_event.html", locals())

        post_data = request.POST.copy()
        post_data['booking_link'] = booking_links

        form = EventForm(post_data or None, request.FILES or None, instance=event)
        event_rules = event.rules.all()
        if form.is_valid():
            form.save()
            event.booking_link = booking_links
            event.save()
            event_rules.delete()
            rules_objects = [EventRules(event=event, text=rule) for rule in rules if rule and rule.strip()]
            EventRules.objects.bulk_create(rules_objects)
            messages.success(request, f"Event updated successfully")
            return redirect('event_management')
    else:
        booking_links = event.booking_link
        rules = [i.text for i in event.rules.all()]

    return render(request, "event/edit_event.html", locals())


# @require_permission("users.edit_events")
from django.contrib.auth.decorators import login_required


@login_required
def create_new_event(request):
    if request.method == "POST":
        booking_links = request.POST.getlist("booking_link")
        links_label = request.POST.getlist("booking_link_label")

        try:
            booking_links = dict(zip(links_label, booking_links))
        except Exception as e:
            print(e)
            messages.error(request, f"Event create failed due to {str(e)}")
            return redirect("event_management")

        post_data = request.POST.copy()
        post_data['booking_link'] = booking_links

        form = EventForm(post_data, request.FILES)
        rules = request.POST.getlist('rules')

        if form.is_valid():
            event = Event.objects.create(
                name=form.cleaned_data['name'],
                logo=form.cleaned_data['logo'],
                booking_link=booking_links,
                date=form.cleaned_data['date'],
                description=form.cleaned_data['description'],
                user=request.user,
                event_type=form.cleaned_data.get('event_type'),
                location=form.cleaned_data.get('location'),
            )

            if form.cleaned_data.get("end_date"):
                event.end_date = form.cleaned_data.get("end_date")
                event.save()

            rules_objects = [EventRules(event=event, text=rule) for rule in rules if rule and rule.strip()]
            EventRules.objects.bulk_create(rules_objects)
            messages.success(request, "Event created successfully.")
            return redirect("event_management")
    return render(request, "event/create_new.html", locals())


@require_permission("users.edit_events")
def event_details(request, pk):
    event = get_object_or_404(Event, id=pk)
    event_teams = event.teams.all()
    grades = SchoolGrade.objects.all()
    sub_admins = User.objects.filter(Q(user_role="sub_admin") | Q(user_role="ar_staff"))

    if request.method == "POST":
        name = request.POST['name']
        grade = request.POST.get('grade')
        gender = request.POST.get('gender')

        teams = Team.objects.filter(name=name, grade=grade, gender=gender)
        if teams.exists():
            team = teams.first()
            # team.grade = grade
            # team.gender = gender
            # team.save()
        else:
            team = Team.objects.create(
                name=name,
                grade=grade,
                gender=gender
            )

        if event_teams.filter(id=team.id).exists():
            messages.error(request, f"{team.name} already exits in check in team.")
            return redirect("event_detail", pk)

        event.teams.add(team)
        event.save()
        messages.success(request, "team added successfully")
        return redirect("event_detail", pk)

    team_id = request.GET.get('id')
    if request.GET.get("action") == "delete" and team_id:
        try:
            event.teams.remove(team_id)
            messages.success(request, "Team remove successfully")
        except Exception as e:
            print(e)
            event.rosters.remove(team_id)
            messages.success(request, "Roster remove successfully")

        event.save()
        return redirect("event_detail", pk)
    return render(request, "event/event_details.html", locals())


# @admin_required
# def event_details(request, pk):
#     event = get_object_or_404(Event, id=pk)
#     event_teams = event.teams.all()
#     if request.method == "POST":
#         name = request.POST['name']
#         teams = Team.objects.filter(name=name)
#         if teams.exists():
#             team = teams.first()
#         else:
#             team = Team.objects.create(name=name)
#
#         if event_teams.filter(id=team.id).exists():
#             messages.error(request, f"{team.name} already exits in check in team.")
#             return redirect("event_detail", pk)
#
#         event.teams.add(team)
#         event.save()
#         messages.success(request, "team added successfully")
#         return redirect("event_detail", pk)
#
#     team_id = request.GET.get('id')
#     if request.GET.get("action") == "delete" and team_id:
#         event.teams.remove(team_id)
#         event.save()
#         messages.success(request, "Team deleted successfully")
#         return redirect("event_detail", pk)
#
#     return render(request, "event/event_details.html", locals())


# @admin_required
# def upload_event_check_in_csv(request, pk):
#     event = get_object_or_404(Event, id=pk)
#     if request.method == "POST":
#         form = UploadCsvForm(request.POST, request.FILES)
#         if form.is_valid():
#             positions = Position.objects.all()
#             playing_styles = PlayingStyle.objects.all()
#             coach_position = {display for value, display in User.coach_position_Choice}
#
#             file = request.FILES['file']
#             df = pd.read_csv(file)
#             data = []
#             exclude_data = []
#             for _, row in df.iterrows():
#                 team_detail = {
#                     "TeamName": row['TeamName'] if pd.notna(row.get('TeamName')) else "",
#                     "FirstName": row['FirstName'] if pd.notna(row.get('FirstName')) else "",
#                     "LastName": row['LastName'] if pd.notna(row.get('LastName')) else "",
#                     "Email": row['Email'] if pd.notna(row.get('Email')) else "",
#                     "Username": row['Username'] if pd.notna(row.get('Username')) else "",
#                     "Position": row['Position'] if pd.notna(row.get('Position')) else "",
#                     "PlayingStyle": row['PlayingStyle'] if pd.notna(row.get('PlayingStyle')) else "",
#                     "JerseyNo": row['JerseyNo'] if pd.notna(row.get('JerseyNo')) else "",
#                     "Role": row['Role'] if pd.notna(row.get('Role')) else "",
#                 }
#
#                 fields = ["TeamName", "FirstName", "LastName", "Email", "Username", "Role"]
#
#                 message = []
#
#                 try:
#                     team_detail['JerseyNo'] = int(team_detail['JerseyNo'])
#                 except:
#                     pass
#
#                 missing_fields = [field for field in fields if not team_detail.get(field)]
#                 # if any(not team_detail.get(field) for field in fields):
#                 if missing_fields:
#                     # message.append("Required fields may be missing data.")
#                     message.append(f"Missing required fields: {', '.join(missing_fields)}")
#
#                 if str(team_detail["Role"]).lower() == "player" and isinstance(team_detail['JerseyNo'], int) is False:
#                     message.append("JerseyNo should be valid integer.")
#
#                 if str(team_detail["Role"]).lower() != "player" and str(team_detail["Role"]).lower() != "coach":
#                     message.append(
#                         f"Invalid {team_detail['Role']} it should be <strong>player</strong> or <strong>coach</strong>")
#
#                 if str(team_detail["Role"]).lower() == "player":
#                     position = positions.filter(name__iexact=team_detail['Position']).first()
#                     playing_style = playing_styles.filter(title__iexact=team_detail['PlayingStyle']).first()
#                     if not position:
#                         message.append(f"Invalid position {team_detail['Position']}")
#                     elif not playing_style:
#                         message.append(f"Invalid Playing style {team_detail['PlayingStyle']}")
#                     elif playing_style and position.id != playing_style.position.id:
#                         message.append(
#                             f"Invalid playing style: '{team_detail['PlayingStyle']}' does not exist for position '{team_detail['Position']}'")
#
#                 elif str(team_detail["Role"]).lower() == "coach":
#                     if team_detail['Position'] not in coach_position:
#                         message.append(f"Invalid coach position {team_detail['Position']}")
#
#                 team_detail['message'] = message
#                 if message:
#                     exclude_data.append(team_detail)
#                 else:
#                     data.append(team_detail)
#             key = random.randint(0, 9999999)
#             cache.set(str(key), data, timeout=60 * 30)
#             messages.success(request, "CSV file uploaded successfully. Please review the extracted data.")
#             data_length = len(data)
#             return render(request, "event/team_csv.html", locals())
#         else:
#             messages.error(request, "Something went wrong.")
#
#     return redirect("event_detail", pk)

@admin_required
def upload_event_check_in_csv(request, pk):
    event = get_object_or_404(Event, id=pk)
    if request.method == "POST":
        form = UploadCsvForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            df = pd.read_csv(file)
            data = []
            for index, row in df.iterrows():
                TeamName = row['TeamName'] if pd.notna(row.get('TeamName')) else ""
                if not TeamName:
                    messages.error(request,
                                   f"Team name is required at index {int(index) + 1} Please check and reupload.")
                    break

                Class = row['Class'] if pd.notna(row.get('Class')) else ""
                Gender = row['Gender'] if pd.notna(row.get('Gender')) else ""
                data.append({
                    "TeamName": TeamName,
                    "Class": Class,
                    "Gender": Gender
                })

            for index, i in enumerate(data):
                if event.teams.filter(name=i['TeamName']).exists():
                    messages.error(request, f"{i['TeamName']} is already exists to this event at index {index}")
                    continue
                try:
                    if i['Gender'].lower() not in ["male", "female", "other"]:
                        messages.error(request, f"{i['Gender']} is not valid gender at index {index}.")
                        continue
                except:
                    pass

                team = Team.objects.create(
                    name=i['TeamName'],
                    grade=i["Class"],
                    gender=i['Gender']
                )
                event.teams.add(team)
                event.save()

            messages.success(request, "Csv upload successfully.")
    return redirect("event_detail", pk)


@admin_required
def insert_event_check_in_csv(request, pk):
    event = get_object_or_404(Event, id=pk)
    if request.method == "POST":
        key = request.POST['key']
        exclude = request.POST.getlist("exclude_rows", [])
        data = cache.get(key)

        sport = Sport.objects.filter(name="basketball").first()
        positions = Position.objects.all()
        playing_styles = PlayingStyle.objects.all()
        # coach_position = {display for value, display in User.coach_position_Choice}

        for index, row in enumerate(data):
            if str(index + 1) in exclude:
                continue

            teams = Team.objects.filter(name=row["TeamName"])
            if teams.exists():
                team = teams.first()
            else:
                team = Team.objects.create(name=row["TeamName"])
            event.teams.add(team)
            event.save()

            user = User.objects.filter(email=row['Email']).first()
            if not user:
                user = User.objects.create_user(
                    first_name=row['FirstName'],
                    last_name=row['LastName'],
                    email=row['Email'],
                    username=row['Username'],
                    user_role=row['Role'],
                )
                if user.user_role == "player":
                    position = positions.filter(name__iexact=row['Position']).first()
                    playing_style = playing_styles.filter(title__iexact=row['PlayingStyle']).first()
                    Player.objects.create(
                        user=user,
                        weight=row.get("Weight"),
                        height=row.get("Height"),
                        sport=sport,
                        jersey_number=row.get("JerseyNo"),
                        position=position,
                        playing_style=playing_style
                    )
                else:
                    user.position = row['Position']
                    user.save()

            #
            EventTeamUser.objects.create(
                event=event,
                user=user,
                team=team,
                created_by=request.user
            )
        messages.success(request, "Data inserted successfully.")

    return redirect("event_detail", pk)


@admin_required
def event_plan_management(request):
    if request.method == "POST":
        if "update_plan" in request.POST:
            # update plan
            plan_id = request.POST.get('plan_id')
            plan = get_object_or_404(EventPlan, id=plan_id)
            form = EventRuleForm(request.POST, instance=plan)
            if form.is_valid():
                plan.name = form.cleaned_data['name']
                plan.description = form.cleaned_data['description']
                plan.price = form.cleaned_data['price']
                plan.features = request.POST.getlist("features")
                plan.save()
                messages.success(request, f"Plan {form.cleaned_data['name']} updated successfully.")
                return redirect("event_plan")
            edit_model_open = True
        else:
            # create new plan
            form = EventRuleForm(request.POST)
            if form.is_valid():
                EventPlan.objects.create(
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data['description'],
                    price=form.cleaned_data['price'],
                    features=request.POST.getlist("features")
                )
                messages.success(request, f"Plan {form.cleaned_data['name']} created successfully.")
                return redirect("event_plan")
            open_add_modal = True
    else:
        form = EventRuleForm()
        if request.GET.get("action") == "delete":
            plan = get_object_or_404(EventPlan, id=request.GET.get('id'))
            plan.delete()
            messages.success(request, f"Plan deleted successfully.")
            return redirect("event_plan")

    plans = EventPlan.objects.all()
    return render(request, "event/plans.html", locals())


@admin_required
def event_check_in_users(request, pk):
    page_number = request.GET.get("page", 1)
    event = get_object_or_404(Event, id=pk)
    # athletes = User.objects.filter(event_check_in__event_id=pk)
    users = EventCheckIn.objects.filter(event=event).order_by("-created_at")
    query = request.GET.get("q")

    if query:
        users = users.filter(Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query))

    paginator = Paginator(users, 100)
    users = paginator.get_page(page_number)
    return render(request, "event/check_in_users.html", locals())


def event_payment_callback(request, action):
    current_site = Site.objects.get_current()
    current_site = current_site.domain

    if action == "success":
        return render(request, "event/event_pay_success.html", locals())

    return render(request, "event/payment_cancel.html", locals())


@admin_required
def transaction_management(request):
    transactions = EventTransaction.objects.all()
    return render(request, "event/transaction-management.html", locals())


@admin_required
def assign_sub_admin(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        sub_admin_ids = request.POST.getlist("sub_admin_ids")
        event.sub_admins.clear()
        for data in sub_admin_ids:
            user_obj = User.objects.get(id=data)
            event.sub_admins.add(user_obj)
            event.save()
        messages.success(request, "Sub-admin has been assigned to the event successfully")

    sub_admins = User.objects.filter(user_role='sub_admin')

    return render(request, "event/event_details.html", locals())

@require_permission("users.edit_events")
def duplicate_event(request, pk):
    original_event = get_object_or_404(Event, id=pk)

    original_rules = list(original_event.rules.all())

    original_event.pk = None
    original_event.name = f"{original_event.name} copy"

    original_event.date = timezone.now() + timedelta(days=365)
    original_event.end_date = None

    original_event.user = request.user
    original_event.save()

    EventRules.objects.bulk_create([
        EventRules(event=original_event, text=rule.text)
        for rule in original_rules
    ])
    messages.success(request,"Please update the event date before saving.")
    return redirect("event_edit", pk=original_event.id)

