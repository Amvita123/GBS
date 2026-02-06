from django.shortcuts import render, redirect
from common.services import admin_required, sub_admin_required
from django.contrib import messages
from .forms import NotificationForm, Notification, PushNotificationForm
from notification.task import push_admin_notification, send_event_notification
from notification.models import PushNotification
from event.models import Event
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404


@sub_admin_required
def push_notification(request):
    events = Event.objects.all()
    if request.method == "POST":
        form = PushNotificationForm(request.POST)
        if form.is_valid():
            notification = PushNotification(
                title=form.cleaned_data['title'],
                message=form.cleaned_data['message'],
                to=form.cleaned_data['to'],
                created_by=request.user,

            )
            if form.cleaned_data.get("schedule"):
                notification.schedule = form.cleaned_data.get("schedule")
                messages.success(request, f"Notification scheduled successfully to {form.cleaned_data['to']}")

            else:
                messages.success(request, f"Notification push successfully to {form.cleaned_data['to']}")
                notification.sent = True
                if form.cleaned_data.get("event"):
                    send_event_notification.delay(
                        event_id=form.cleaned_data['event'].id,
                        title=form.cleaned_data['title'],
                        message=form.cleaned_data['message']
                    )
                else:
                    push_admin_notification.delay(
                        user_type=form.cleaned_data['to'],
                        title=form.cleaned_data['title'],
                        message=form.cleaned_data['message']
                    )

            if form.cleaned_data.get("event"):
                notification.event = form.cleaned_data.get("event")

            notification.save()

            return redirect("send_push_notification")
    else:
        form = PushNotificationForm()
    return render(request, "notification/push_message.html", locals())


@admin_required
def select_notification(request):
    return render(request, "notification/notification_select.html")


@admin_required
def notification_history(request, action):
    actions = ['history', "upcoming"]
    if action not in actions:
        messages.error(request,  f"Sorry we could n't found {action} notification.")
        return redirect("send_push_notification")

    page_number = request.GET.get("page", 1)
    notifications = PushNotification.objects.filter(sent=True if action == "history" else False)
    paginator = Paginator(notifications, 25)
    notifications = paginator.get_page(page_number)
    events = Event.objects.all()
    notifications_to = ["player", "fan", "coach", "sub-admin"]
    return render(request, "notification/history.html", locals())


@admin_required
def update_upcoming_notification(request):
    if request.method == "POST":
        notification = get_object_or_404(PushNotification, id=request.POST['notification_id'])
        form = PushNotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification update successfully.")
        else:
            print(form.errors)

    return redirect("notification_history", action='upcoming')



