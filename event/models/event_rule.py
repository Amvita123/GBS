from django.db import models


class EventRules(models.Model):  # It's  event details changed rules to details
    event = models.ForeignKey("event.Event", related_name='rules', on_delete=models.CASCADE)
    text = models.TextField()
