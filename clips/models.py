from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import get_valid_filename


def clip_upload_path(instance, filename):
    """保存先のパス。日付とカメラで分けて、後から探しやすくする。

    taken_at はUTCで持っているため、フォルダ分けは日本時間に直してから行う
    (深夜に保存したクリップが前日のフォルダに入るのを防ぐ)。
    """
    taken = timezone.localtime(instance.taken_at)
    extension = filename.rsplit(".", 1)[-1]
    return f"clips/{taken:%Y/%m/%d}/camera{instance.camera_id}_{taken:%H%M%S}.{extension}"


class Clip(models.Model):
    """ユーザーが保存した映像。実ファイルはMEDIA_ROOT配下に置き、DBにはパスだけ持つ。

    2種類を同じテーブルで持つ(media_typeで区別する)。

    - image … スクリーンショット。ある瞬間の1コマ
    - video … クリップ。開始から終了までを切り取った動画
    """

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
    # クリップ(動画)の長さ。スクリーンショットは0
    seconds = models.PositiveIntegerField("長さ(秒)", default=0)
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

    @property
    def is_video(self):
        return self.media_type == self.VIDEO

    @property
    def download_name(self):
        """PCに保存したときに中身が分かるファイル名。

        報告書に添付することを想定し、タイトル・カメラ・日時を並べる。
        """
        taken = timezone.localtime(self.taken_at)
        extension = self.file.name.rsplit(".", 1)[-1]
        base = "_".join([
            self.title,
            self.camera.server.name,
            self.camera.name,
            taken.strftime("%Y%m%d_%H%M%S"),
        ])
        # ファイル名に使えない文字を落とし、長くなりすぎないようにする
        return f"{get_valid_filename(base)[:100]}.{extension}"

    @property
    def png_name(self):
        """PNGとして配るときのファイル名。"""
        return f"{self.download_name.rsplit('.', 1)[0]}.png"

    def movie_name(self, extension):
        """動画として配るときのファイル名。"""
        return f"{self.download_name.rsplit('.', 1)[0]}.{extension}"
