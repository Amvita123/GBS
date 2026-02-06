from celery import shared_task
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import datetime
from datetime import datetime, timedelta
from django.utils import timezone
from twilio.rest import Client

from users.models import IdentityVerification, User
from notification.task import send_user_action_notification
from notification.models import PushNotification


@shared_task
def auth_mail_send(subject, html_message, user_email):
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [user_email],
            html_message=html_message
        )
        return "mail sent successfully."
    except Exception as e:
        return f"error to send mail: \n {str(e)}"


@shared_task
def send_sub_admin_login_details(username, email, password, phone_number):
    html_message = render_to_string('mail/sub_admin_credential.html', {
        'username': username.title(),
        'email': email,
        "year": str(datetime.now().year),
        "password": password
    })
    subject = 'Athlete Rated access point.'
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [email],
            html_message=html_message
        )
    except Exception as e:
        print(f"error to send mail: \n {str(e)}")

    sms_body = f"""Hello {username}, Your account has been created successfully.Username: {username} Password: {password} Login at: https://athleterated.com/login/?next=/
          (Please change your password after first login.)
          """
    send_sms.delay(phone_number, sms_body)
    return "sub admin credential sent successfully."


@shared_task
def send_sms(phone_number, sms_body):
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            # from_='+17755103845',
            from_='+18134384773',
            body=sms_body,
            to=phone_number
        )
        print(message.sid)
    except Exception as e:
        print(str(e))

    return "send twilio sms"


@shared_task
def send_password_mail(username, email, password, phone_number):
    html_message = render_to_string('mail/new_password.html', {
        'username': username.title(),
        "year": str(datetime.now().year),
        "password": password
    })
    subject = 'Athlete Rated Password'
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [email],
            html_message=html_message
        )
    except Exception as e:
        print(f"error to send mail: \n {str(e)}")

    try:
        sms_body = f"""Hello {username}, Your password has been reset please login with new Password: {password}
              (Please change your password after first login.)
              """
        send_sms.delay(phone_number, sms_body)
    except Exception as e:
        print(e)

    return "player credential resent successfully."

@shared_task
def send_verification_expiry_email(username, email, role, days_left):
    html_message = render_to_string(
        "mail/verification_expiry.html",
        {
            "username": username.title(),
            "role": role,
            "days_left": days_left,
            "year": datetime.now().year,
        }
    )
    subject = "AthleteRated Verification Status"
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [email],
        html_message=html_message,
    )
    return "verification email sent successfully."

@shared_task
def handle_verification_expiry():
    today = timezone.now().date()
    notify_date = today - timedelta(days=362)

    remender_verifications = IdentityVerification.objects.filter(
        user__user_role__in=["player", "coach", "fan"],
        status="accept",
        updated_at__date=notify_date
    )

    for verification in remender_verifications:
        user = verification.user
        verification.status = "expiring"
        verification.save()

        send_verification_expiry_email.delay(
            user.username,
            user.email,
            user.user_role,
            3
        )

        message = f"{user.username} Your {user.user_role} verification will expire in 3 days. Please renew to continue using premium features."
        send_user_action_notification.delay(
            title="Verification expiry in 3 days",
            message=message,
            sender="admin",
            receiver=user.username,
            action="verification_expiry"
        )

    expired_verifications = IdentityVerification.objects.filter(
        user__user_role__in=["player", "coach", "fan"],
        status__in=["accept", "expiring"],
        updated_at__date__lte=today - timedelta(days=365)
    )

    for verification in expired_verifications:
        user = verification.user
        verification.status = "expired"
        verification.save()

        user.is_identity_verified = False
        user.save()

        send_verification_expiry_email.delay(
            user.username,
            user.email,
            user.user_role,
            0
        )

        message = f"{user.username} Your {user.user_role} verification will expire."
        send_user_action_notification.delay(
            title="Verification Expiry",
            message=message,
            sender="admin",
            receiver=user.username,
            action="verification_expiry"
        )

    return (
        f"Reminder sent: {remender_verifications.count()}, "
        f"Users disabled: {expired_verifications.count()}"
    )