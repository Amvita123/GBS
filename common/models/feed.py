from common.models import CommonFields
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import cv2
from django.core.files.storage import default_storage
import asyncio

video_extension = ['mp4', 'mov', 'avi', 'mkv', 'webm']


async def async_delete_file(path):
    await asyncio.sleep(5)
    default_storage.delete(path)


def validate_video(value):
    if str(value.name).split(".")[-1] in video_extension:
        temp_path = default_storage.save(f"temp_videos/{value.name}", value)
        temp_file_path = default_storage.path(temp_path)
        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            raise ValidationError("Could not open video file.")
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        seconds = round(frames / fps)
        cap.release()
        default_storage.delete(temp_path)

        if seconds > 30:
            raise ValidationError("Video length must be 30 seconds or less.")
        return value


class Feed(CommonFields):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="poster")
    caption = models.TextField()
    link = models.URLField(blank=True, default="")
    # badge = models.ForeignKey(
    #     "players.Badge",
    #     on_delete=models.DO_NOTHING,
    #     null=True, blank=True,
    # )  # only player can
    # location = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(
        upload_to="feeds/",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', "heic", ] + video_extension),
            validate_video
        ],
        blank=True
    )
    tags = models.ManyToManyField("users.User", blank=True)
    roster = models.ForeignKey("coach.Roster", on_delete=models.CASCADE, null=True, blank=True, related_name="roster_feed")
    like = models.BigIntegerField(default=0)
    liker = models.ManyToManyField("users.User", related_name="likers")
    thumbnail = models.ImageField(upload_to="thumbnails/", validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', "heic", ])
        ], null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def badges_objects(self):
        return [badge for badge in self.feed_badge.all()] if hasattr(self, 'feed_badge') else []
