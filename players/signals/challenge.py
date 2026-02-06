from django.db.models.signals import post_save
from django.dispatch import receiver
from players.models import Challenge


# @receiver(post_save, sender=Challenge)
# def player_challenge_win_loss(sender, instance, created, **kwargs):
#     if not created:
#         print(f"Product '{instance.name}' was updated.")


