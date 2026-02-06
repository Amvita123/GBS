from django.contrib import messages
from players.models import Badge


def validate_badge_assign(request, badges, badge_level_name):
    badge_id_level_name = {}
    for selected_badge in badge_level_name.split(','):
        badge_id_level = selected_badge.split('_')
        badge_id = str(badge_id_level[0]).replace(" ", '')
        try:
            level_name = badge_id_level[1]
            if badge_id in badge_id_level_name:
                level_name_list = badge_id_level_name[badge_id]
                level_name_list.append(level_name)
                badge_id_level_name[badge_id] = level_name_list

                # badge_id_level_name[badge_id] = level_name_list.append(level_name)
            else:
                badge_id_level_name[badge_id.replace(" ", '')] = [level_name]
        except Exception as e:
            print("errr ", e)
            badge_id_level_name[badge_id] = []
            continue

    # print(badges)
    for badge, badges_levels in badge_id_level_name.items():
        for level in badges_levels:
            if level == "silver":
                if "bronze" not in badges_levels:
                    messages.error(request, "Cannot assign Silver badge. Assign Bronze first, or remove both.")
                    return False
            elif level == "gold":
                if "silver" not in badges_levels:
                    messages.error(request, "Cannot assign Gold badge. Assign Bronze and Silver first, or remove all.")
                    return False
    return True
