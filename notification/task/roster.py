from celery import shared_task
from notification.models import Notification
from coach.models import InvitePlayer
from users.models import User
from .sender import send_notification


@shared_task
def manual_user_invitation_notification(email):
    invitations = InvitePlayer.objects.select_related("roster").filter(
        email=email, status="pending").order_by("roster_id").distinct("roster")

    user = User.objects.filter(email=email).first()
    if not user:
        raise ValueError(f"error at invitation processing at signup"
                         f": user {email} not found to database ")

    for invitation in invitations:
        try:
            if Notification.objects.select_related("to_user").filter(objects_id=invitation.id, to_user__email=email).exists() is False:
                Notification.objects.create(
                    to_user_id=user.id,
                    title="Roster Invitation",
                    message=f"Roster {invitation.roster.name.title()} has invited you to join",
                    action="roster_invitation",
                    objects_id=invitation.id,
                    is_action=True,

                )
                send_notification.delay(
                    username=user.username,
                    title="Roster Invitation",
                    message=f"Roster {invitation.roster.name.title()} has invited you to join"
                )
        except Exception as e:
            print(e)

    return "Invitation notification process successfully."

