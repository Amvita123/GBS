from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission


# @receiver(post_migrate)
# def create_default_groups(sender, **kwargs):
#     if sender.name != "users":  # app name
#         return
#
#     # ---- Create Groups ----
#     ar_staff_group, _ = Group.objects.get_or_create(name="AR Staff")
#     event_director_group, _ = Group.objects.get_or_create(name="Event Director")
#
#     # ---- Load Permissions ----
#     perms = Permission.objects.filter(content_type__app_label="core")
#
#     identity_v = perms.get(codename="identity_verification")
#     edit_events = perms.get(codename="edit_events")
#     revenue_share = perms.get(codename="view_revenue_share")
#     event_all = perms.get(codename="view_all_event")
#
#     # ---- Assign Permissions ----
#
#     # AR Staff (base permissions)
#     ar_staff_group.permissions.add(event_all)
#
#     # Optional permissions (only assign if needed)
#     # You can assign these to specific users later
#     # ar_staff_group.permissions.add(identity_v, edit_events, revenue_share)
#
#     # Event Director (limited permissions)
#     event_director_group.permissions.add(edit_events)

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    # Only run when the 'users' app migration completes
    if sender.label != "users":
        return

    # Now the permissions are guaranteed to exist
    perms = Permission.objects.filter(content_type__app_label="users")

    # Fetch custom permissions safely
    identity_v = perms.filter(codename="identity_verification").first()
    edit_events = perms.filter(codename="edit_events").first()
    revenue = perms.filter(codename="view_revenue_share").first()
    manage_all = perms.filter(codename="manage_all_events").first()

    # Create Groups
    ar_staff, _ = Group.objects.get_or_create(name="AR Staff")
    event_director, _ = Group.objects.get_or_create(name="Event Director")

    # Assign permissions if they exist
    if identity_v:
        ar_staff.permissions.add(identity_v)
    if edit_events:
        ar_staff.permissions.add(edit_events)
    if revenue:
        ar_staff.permissions.add(revenue)
    if manage_all:
        ar_staff.permissions.add(manage_all)

    # Event Director gets only limited permissions
    if edit_events:
        event_director.permissions.add(edit_events)

