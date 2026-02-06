from django.contrib import messages
from players.models import SchoolGrade
from coach.models import CoachType


def users_management_actions(request, users):
    user_id = request.GET.get("id")

    if user_id:
        try:
            if request.GET.get("action") == "delete_grade":
                SchoolGrade.objects.filter(id=user_id).first().delete()
                messages.success(request, "Grade has been deleted successfully.")
                return True

            elif request.GET.get("action") == "delete_coach_type":
                CoachType.objects.filter(id=user_id).first().delete()
                messages.success(request, "Coach type has been deleted successfully.")
                return True

            user = users.get(id=user_id)
            if request.GET.get("action") == "delete":
                user.delete()
            elif request.GET.get("action") == "activate":
                user.is_active = True
                user.save()
            elif request.GET.get("action") == "deactivate":
                user.is_active = False
                user.save()
            messages.success(request, f"{user.username} has {request.GET.get('action')} successfully.")
            return True
        except Exception as e:
            messages.error(request, str(e))
