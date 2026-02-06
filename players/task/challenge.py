from celery import shared_task
from players.models import Challenge
from datetime import datetime
from notification.task import send_user_action_notification


@shared_task
def challenge_simulation():
    challenges = Challenge.objects.filter(result_date=datetime.now().date(), is_accepted=True, winner__isnull=True)

    for challenge in challenges:
        squad_a_score = sum(
            [(9 - SqA.player_profile.position.rating) * (21 - SqA.player_profile.playing_style.archetype_rating)
             for SqA in challenge.first_squad.players.all()]
        )
        squad_b_score = sum([
            (9 - SqB.player_profile.position.rating) * (21 - SqB.player_profile.playing_style.archetype_rating)
            for SqB in challenge.second_squad.players.all()
        ])

        first_squad = challenge.first_squad
        second_squad = challenge.second_squad

        if squad_a_score > squad_b_score:
            challenge.winner = challenge.first_squad
            # win & loss update
            first_squad.win = first_squad.win + 1
            second_squad.loss = second_squad.loss + 1
        else:
            challenge.winner = challenge.second_squad
            # win & loss update
            second_squad.win = second_squad.win + 1
            first_squad.loss = first_squad.loss + 1

        first_squad.save()
        second_squad.save()

        challenge.point_first_squad = squad_a_score
        challenge.point_second_squad = squad_b_score
        challenge.status = "completed"
        challenge.save()

        try:
            first_squad = challenge.first_squad
            first_squad.win = first_squad.win
        except Exception as e:
            print(e)

        send_user_action_notification.delay(
            sender=challenge.first_squad.created_by.username,
            receiver=challenge.second_squad.created_by.username,
            message=f"Result has been out of your challenge.",
            action="challenge_result",
            object_id=f"{challenge.id}"
        )

        send_user_action_notification.delay(
            receiver=challenge.first_squad.created_by.username,
            sender=challenge.second_squad.created_by.username,
            message=f"Result has been out of your challenge.",
            action="challenge_result",
            object_id=f"{challenge.id}"
        )

    return "challenge result has be calculated"

