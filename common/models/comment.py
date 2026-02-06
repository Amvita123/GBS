from django.db import models
from common.models import CommonFields


class Comment(CommonFields):
    user = models.ForeignKey("users.User",
                             on_delete=models.CASCADE, )  # limit_choices_to={"user_role__in": ["fan", "coach"]}
    feed = models.ForeignKey("common.Feed", on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
