"""映像取得の切り替え層。

NxWitnessは社内LAN内にしか存在せず、公開レビュー環境からは到達できない。
そのため映像の取得元を抽象化し、環境変数 VIDEO_SOURCE で差し替える。

- mock … アプリ側で生成した疑似映像を返す(公開環境・テスト用)
- nx   … NxWitness APIを参照する(社内LAN内)

ビューからNxWitness APIを直接呼ばず、必ずこの層を経由させること。
"""

from abc import ABC, abstractmethod

from django.conf import settings
from django.urls import reverse

# ラインの種類ごとに、疑似映像に流す製品の見た目を変える
PRODUCT_SHAPES = {
    "缶": "can",
    "瓶": "bottle",
    "樽": "keg",
}
DEFAULT_SHAPE = "can"


class VideoSource(ABC):
    """映像取得元の共通インターフェース。"""

    @abstractmethod
    def live_image_url(self, camera):
        """ライブ映像(静止画)の取得先URLを返す。"""

    @abstractmethod
    def is_available(self):
        """映像を取得できる状態かどうか。"""


class MockVideoSource(VideoSource):
    """アプリ側で生成した疑似映像を返す。

    実カメラが無い環境でも画面の動作を確認できるようにするためのもの。
    静止画(SVG)を定期的に取得し直すことで、帯域を使わずにライブらしく見せる。
    """

    def live_image_url(self, camera):
        return reverse("cameras:live_image", args=[camera.pk])

    def is_available(self):
        return True

    def product_shape(self, camera):
        """カメラが属するラインから、流れる製品の形を決める。"""
        line = camera.server.line
        for keyword, shape in PRODUCT_SHAPES.items():
            if keyword in line:
                return shape
        return DEFAULT_SHAPE


class NxVideoSource(VideoSource):
    """NxWitness APIから映像を取得する。

    認証方式とエンドポイントはNxWitnessのバージョンで異なるため、
    社内LAN内での疎通確認(Issue #25)に合わせて実装する。
    設定は settings の NX_BASE_URL / NX_USERNAME / NX_PASSWORD を使う。
    """

    def live_image_url(self, camera):
        raise NotImplementedError(
            "NxWitness APIからの映像取得は未実装です(Issue #25の疎通確認後に対応)。"
        )

    def is_available(self):
        return bool(settings.NX_BASE_URL)


def get_video_source():
    """設定に応じた映像取得元を返す。"""
    if settings.VIDEO_SOURCE == "nx":
        return NxVideoSource()
    return MockVideoSource()
