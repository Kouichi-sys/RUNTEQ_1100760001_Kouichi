from django.conf import settings
from django.db import models
from django.utils import timezone


def clip_upload_path(instance, filename):
    """保存先のパス。日付とカメラで分けて、後から探しやすくする。

    taken_at はUTCで持っているため、フォルダ分けは日本時間に直してから行う
    (深夜に保存したクリップが前日のフォルダに入るのを防ぐ)。
    """
    taken = timezone.localtime(instance.taken_at)
    extension = filename.rsplit(".", 1)[-1]
    return f"clips/{taken:%Y/%m/%d}/camera{instance.camera_id}_{taken:%H%M%S}.{extension}"


class Clip(models.Model):
    """ユーザーが保存した映像。実ファイルはMEDIA_ROOT配下に置き、DBにはパスだけ持つ。"""

    IMAGE = "image"
    VIDEO = "video"
    MEDIA_TYPE_CHOICES = [
        (IMAGE, "静止画"),
        (VIDEO, "動画"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clips",
        verbose_name="保存したユーザー",
    )
    camera = models.ForeignKey(
        "cameras.Camera",
        on_delete=models.CASCADE,
        related_name="clips",
        verbose_name="カメラ",
    )
    title = models.CharField("タイトル", max_length=100)
    file = models.FileField("ファイル", upload_to=clip_upload_path)
    media_type = models.CharField(
        "種別", max_length=10, choices=MEDIA_TYPE_CHOICES, default=IMAGE
    )
    taken_at = models.DateTimeField("映像取得日時")
    memo = models.TextField("メモ", blank=True)

    class Meta:
        # ER図に合わせてテーブル名をclipsにする
        db_table = "clips"
        verbose_name = "クリップ"
        verbose_name_plural = "クリップ"
        # マイページでは新しいものから見たい
        ordering = ("-taken_at",)

    def __str__(self):
        return self.title
