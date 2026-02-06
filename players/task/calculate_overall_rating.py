from celery import shared_task
from players.models import PlayerBadges, Player
from notification.task import send_single_user_admin_notification


@shared_task
def cal_overall_rating(user_id):
    badge_weights = [int(player_badge.badge.weight) for player_badge in PlayerBadges.objects.select_related(
        "user", "badge", "badge_level"
    ).filter(user__id=user_id)]
    overall_rating = 50 + ((sum(badge_weights) / 100) * (99-50))
    player_profile = Player.objects.filter(user__id=user_id).first()
    rating = player_profile.overall_rating

    player_profile.overall_rating = overall_rating
    player_profile.save()

    if rating != overall_rating:
        send_single_user_admin_notification.delay(
            username=player_profile.user.username,
            user_id=player_profile.user.id,
            message=f"Your rating has updated. Check your profile to see your latest achievement.",
            title="New Rating Earned!"
        )

    return f"player: {user_id} overall rating {overall_rating}"


