from django import template
from players.models import BadgeLevel
from django.db.models import Q
import os

register = template.Library()


@register.filter
def check_badge_assign(earned_badges, args):
    if earned_badges.filter(badge__id=args[0], badge_level__name=args[1]):
        return True

    return False


@register.filter
def concat_args(val1, val2):
    return [val1, val2]


@register.filter
def check_template(temp, templates):
    # print("temp ", temp.replace(" ", '').lower())
    # for i in templates:
        # print("temp.replace ", temp.replace(" ", ''))
        # print("i.replace ", i.replace(" ", ''))
    if temp.replace(" ", '').lower() in templates:
        return True

    return False


@register.filter
def check_is_badge_assigned(earned_badges, badge):
    if earned_badges.filter(badge=badge).exists():
        return True
    return False


@register.filter
def check_badge_level(badge):
    if BadgeLevel.objects.select_related('badge').filter(
            Q(name='bronze'.lower()) | Q(name='silver'.lower()) | Q(name='gold'.lower()),
            badge__id=badge.id
    ).exists():
        return True

    return False


VIDEO_EXTS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']


@register.filter
def is_video(file_url):
    if not file_url:
        return False
    ext = os.path.splitext(str(file_url).lower())[1]
    if ext in VIDEO_EXTS:
        return True
    return False


@register.filter
def video_mime_type(file_url):
    ext = os.path.splitext(str(file_url).lower())[1]
    return {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
    }.get(ext, 'video/mp4')
