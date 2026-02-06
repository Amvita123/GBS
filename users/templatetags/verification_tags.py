from django import template
from ..models import IdentityVerification
from dashboard.models import AdminSubscription
from datetime import datetime

register = template.Library()


@register.simple_tag
def user_verification_status(user):
    """
    Returns 'first_submit' if user has never submitted a verification,
    or 'resubmit' if they already have one or more previous submissions.
    """
    total_submissions = IdentityVerification.objects.filter(user=user).count()

    if total_submissions == 1:
        return "first_submit"
    elif total_submissions == 2:
        return "resubmit"
    else:
        msg = f"resubmit - {total_submissions}"
        return msg


@register.simple_tag
def get_verification(user):
    try:
        verification_obj = IdentityVerification.objects.filter(user=user, status="accept").first()
        return verification_obj

    except Exception as e:
        print(e)


@register.simple_tag
def check_subscription(user):
    today = datetime.now().date()
    if AdminSubscription.objects.filter(
            user=user,
            start_date__lte=today,
            end_date__gte=today
    ).exists():
        return True

    return False

@register.simple_tag
def get_referer_revenue(referer):
    IdentityVerification.objects.filter(refer_by=referer)
