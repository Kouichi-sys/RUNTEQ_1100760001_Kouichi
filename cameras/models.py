from django.db import models


class Server(models.Model):
    """NxWitnessサーバー。製造ラインごとに1台置かれ、カメラ列の単位になる。"""

    name = models.CharField("サーバー名", max_length=100)
    address = models.CharField("接続先アドレス", max_length=255)
    line = models.CharField("製造ライン名", max_length=100)

    class Meta:
        # ER図に合わせてテーブル名をserversにする
        db_table = "servers"
        verbose_name = "サーバー"
        verbose_name_plural = "サーバー"
        # 現場の並び(缶→瓶→樽など)をそのまま出したいので、登録した順に表示する
        ordering = ("id",)

    def __str__(self):
        return self.name


class Camera(models.Model):
    """サーバーに接続されたカメラ。1台のサーバーに複数台ぶら下がる。"""

    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name="cameras",
        verbose_name="サーバー",
    )
    name = models.CharField("カメラ名", max_length=100)

    class Meta:
        db_table = "cameras"
        verbose_name = "カメラ"
        verbose_name_plural = "カメラ"
        # 工程の流れ(充填→巻締→パレタイズ)の順に見せたいので、登録した順に表示する
        ordering = ("server", "id")

    def __str__(self):
        return f"{self.server.name} / {self.name}"
