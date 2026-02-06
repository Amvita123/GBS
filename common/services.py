from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.utils.timezone import now
from django.contrib.humanize.templatetags.humanize import naturaltime


def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=f"{settings.LOGIN_URL}"):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_superuser or u.user_role == "ar_staff"),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def sub_admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=f"{settings.LOGIN_URL}"):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_superuser or u.user_role == "sub_admin" or u.user_role == "ar_staff"),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def human_readable_timesince(dt):
    delta = now() - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 120:
        return "a minute ago"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minutes ago"
    elif seconds < 7200:
        return "an hour ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hours ago"
    elif seconds < 172800:
        return "a day ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} days ago"
    elif seconds < 1209600:
        return "a week ago"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} weeks ago"
    elif seconds < 5184000:
        return "a month ago"
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} months ago"
    elif seconds < 63072000:
        return "a year ago"
    else:
        years = int(seconds // 31536000)
        return f"{years} years ago"


def smart_timesince(dt):
    delta = now() - dt
    if delta.days > 3:
        return dt.strftime("%d-%b" if dt.year == now().year else "%d-%b,%Y")
    return naturaltime(dt)


def require_permission(*perms):
    """
    Centralized decorator that allows:
    - superuser
    - OR any user having any of the given permissions
    """
    def decorator(view_func):
        def check(user):
            if not user.is_active:
                return False

            # superuser always allowed
            if user.is_superuser:
                return True

            # check custom permissions
            for perm in perms:
                if user.has_perm(f"users.{perm}"):
                    return True

            return False

        return user_passes_test(check)(view_func)
    return decorator


