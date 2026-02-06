from django.db import models
from .common import CommonFields


class ReportReasons(models.Model):
    reason = models.TextField(unique=True)

    def __str__(self):
        return self.reason


class FeedReport(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="reported_by")
    feed = models.ForeignKey("common.Feed", on_delete=models.CASCADE, related_name="reported_feed")
    reason = models.ForeignKey(ReportReasons, on_delete=models.CASCADE, related_name="feed")
    other_reason = models.TextField(null=True, blank=True)
