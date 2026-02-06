from django import template
from urllib.parse import urlparse
from datetime import datetime

register = template.Library()


@register.filter
def get_host(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname


@register.filter
def get_event_status(date):
    if date < datetime.now():
        return "completed"
    else:
        return "upcoming"

