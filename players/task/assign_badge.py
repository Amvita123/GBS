from celery import shared_task
from players.models import BadgeLevel, FeedBadgeRating, PlayerBadges
from django.db.models import Q
from .calculate_overall_rating import cal_overall_rating


@shared_task
def player_badge_assign(rate_badge_id):
    rate_badge = FeedBadgeRating.objects.filter(rate_badge__id=rate_badge_id)
    rates_count = {
        i: rate_badge.filter(rating=i).count()
        for i in range(1, 6)
    }

    post_user = rate_badge.first().rate_badge.feed.user
    rated_badge = rate_badge.first().rate_badge.badge

    for level in ['green', "orange", "yellow"]:
        for rating, user_count in rates_count.items():
            rate_condition = BadgeLevel.objects.filter(
                (Q(weight__lt=user_count) | Q(weight=user_count)), rating=rating, name=level
            )

            if rate_condition.exists():
                match_rate_level = rate_condition.first()
                player_assigned_badges = PlayerBadges.objects.select_related(
                    "user", "badge", "badge_level"
                ).filter(user=post_user, badge=rated_badge)

                if player_assigned_badges.exists():
                    assigned_badge_level = player_assigned_badges.first()
                    if assigned_badge_level.badge_level.name == match_rate_level.name:
                        break
                    assigned_badge_level.badge_level = match_rate_level
                    assigned_badge_level.save()
                else:
                    PlayerBadges.objects.create(
                        user=post_user,
                        badge=rated_badge,
                        badge_level=match_rate_level,
                        point=BadgeLevel.level_points()[level]
                    )
    cal_overall_rating.delay(post_user.id)
    return f"{level} assigned to {post_user.username}"


