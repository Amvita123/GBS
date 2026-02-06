import django_filters
from players.models import Badge
from rest_framework.permissions import BasePermission
from common.models import Skill
import os
import tempfile
from moviepy import VideoFileClip
import uuid
from django.conf import settings


class PostFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_admin_assignable = django_filters.BooleanFilter()

    class Meta:
        model = Badge
        fields = ['name', "is_admin_assignable"]


class IsPlayerUser(BasePermission):
    """
    Custom permission to allow only users with role 'player' to create objects.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role == "player"


class SkillFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Skill
        fields = ['name']


def post_video_thumbnail(value):
    ext = os.path.splitext(value.name)[-1].lower()
    allowed_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    if ext not in allowed_exts:
        return False, f"File extension “{ext}” is not allowed"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        for chunk in value.chunks():
            temp_file.write(chunk)
        temp_file.flush()

    try:
        clip = VideoFileClip(temp_file.name)
        duration = clip.duration

        if duration > 30:
            return False, "Video must be 30 seconds or shorter."

        def thumbnail_generator():
            thumbnail_name = f"{uuid.uuid4()}.jpg"
            thumbnail_dir = os.path.join(settings.MEDIA_ROOT, "thumbnails")
            os.makedirs(thumbnail_dir, exist_ok=True)
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)
            clip.save_frame(thumbnail_path, t=1.0)  # frame at 1s
            return thumbnail_name

        return True, f"thumbnails/{thumbnail_generator()}"

    except Exception as e:
        print("error at video thumbnail generate -- ", e)
    return False, "Could not read video file."


# def post_video_thumbnail(value):
#     ext = os.path.splitext(value.name)[-1].lower()
#     allowed_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
#
#     if ext not in allowed_exts:
#         return False, f"File extension “{ext}” is not allowed"
#
#     try:
#         # Save uploaded file to temp file on disk
#         with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
#             for chunk in value.chunks():
#                 temp_file.write(chunk)
#             temp_file_path = temp_file.name  # save path before closing
#
#         # At this point, temp_file is closed and fully flushed
#         clip = VideoFileClip(temp_file_path)
#         duration = clip.duration
#
#         if duration > 30:
#             clip.close()
#             os.remove(temp_file_path)
#             return False, "Video must be 30 seconds or shorter."
#
#         # Generate and save thumbnail
#         thumbnail_name = f"{uuid.uuid4()}.jpg"
#         thumbnail_dir = os.path.join(settings.MEDIA_ROOT, "thumbnails")
#         os.makedirs(thumbnail_dir, exist_ok=True)
#         thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)
#
#         clip.save_frame(thumbnail_path, t=1.0)  # Save frame at 1 second
#         clip.close()
#
#         # Clean up temp file
#         os.remove(temp_file_path)
#
#         return True, f"thumbnails/{thumbnail_name}"
#
#     except Exception as e:
#         print("Error generating video thumbnail:", str(e))
#         return False, "Could not read video file."

