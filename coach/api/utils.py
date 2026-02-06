from django.template.loader import render_to_string
from datetime import datetime
from users.task import auth_mail_send


def coach_5vs5_simulation(first_squad, second_squad):
    first_squad_score = sum(
        [(9 - SqA.player_profile.position.rating) * (21 - SqA.player_profile.playing_style.archetype_rating)
         for SqA in first_squad.players.all()]
    )
    second_squad_score = sum([
        (9 - SqB.player_profile.position.rating) * (21 - SqB.player_profile.playing_style.archetype_rating)
        for SqB in second_squad.players.all()
    ])

    if first_squad_score > second_squad_score:
        return f"{first_squad.name} wins."

    return f"{second_squad.name} wins."


def coach_5vs5_player_simulation(first_group, second_group):
    first_squad_score = sum(
        [(9 - SqA.player_profile.position.rating) * (21 - SqA.player_profile.playing_style.archetype_rating)
         for SqA in first_group]
    )
    second_squad_score = sum([
        (9 - SqB.player_profile.position.rating) * (21 - SqB.player_profile.playing_style.archetype_rating)
        for SqB in second_group
    ])

    if first_squad_score > second_squad_score:
        point = first_squad_score - second_squad_score
        return f"Team A wins with {point} {'points' if point > 1 else 'point'}, Team B scores {second_squad_score} & A {first_squad_score}."

    point = second_squad_score - first_squad_score
    return f"Team B wins with {point} {'points' if point > 1 else 'point'}, Team A scores {first_squad_score} & B {second_squad_score}."


def send_roster_invitation_mail(invitation_obj, coach_name):
    androidLink = "https://play.google.com/store/apps/details?id=com.athleterated.athlete_rated"
    iosLink = "https://apps.apple.com/us/app/athleterated/id6748231721"
    context = {
        'recipient_name': invitation_obj.name.title(),
        'roster_name': invitation_obj.roster.name.title(),
        'coach_name': coach_name,
        'sport': invitation_obj.roster.organization.sport.name.title(),
        'season': invitation_obj.roster.grade.name if invitation_obj.roster.grade else "",
        'app_store_link': iosLink,
        'play_store_link': androidLink,
        'year': datetime.now().year,
    }

    html_message = render_to_string('mail/roster_invitation.html', context)
    subject = 'Athlete Rated Roster Invitation'
    auth_mail_send.delay(subject, html_message, invitation_obj.email)

