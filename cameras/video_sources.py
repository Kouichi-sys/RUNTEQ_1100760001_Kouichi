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

    @abstractmethod
    def stream_markup(self, camera, now):
        """カメラ個別の画面に埋め込む、動き続ける映像のHTMLを返す。

        mockはCSSアニメーション付きのSVG、実機ではNxWitnessのストリームを
        再生する <video> を返すことを想定している。
        """

    @abstractmethod
    def capture(self, camera, now):
        """その時点の1コマを切り出す(スクリーンショット)。

        (ファイルの中身(bytes), 拡張子, media_type) を返す。
        保存処理はこの戻り値をそのままファイルに書き出す。
        """

    @abstractmethod
    def capture_range(self, camera, start_at, end_at):
        """開始から終了までを切り取る(クリップ)。

        戻り値の形はcaptureと同じ。実機ではNxWitnessから該当区間の
        動画を取得することを想定している。
        """

    @abstractmethod
    def export_movie(self, camera, start_at):
        """メールで共有できる形式の動画を返す。(bytes, 拡張子)

        mockの保存形式(SVG)は受け取った人が開きにくいため、
        渡すときだけ扱いやすい形に変換する。実機は保存したmp4を
        そのまま渡すので、この変換は使わない。
        """


class MockVideoSource(VideoSource):
    """アプリ側で生成した疑似映像を返す。

    実カメラが無い環境でも画面の動作を確認できるようにするためのもの。
    静止画(SVG)を定期的に取得し直すことで、帯域を使わずにライブらしく見せる。
    """

    def live_image_url(self, camera):
        return reverse("cameras:live_image", args=[camera.pk])

    def is_available(self):
        return True

    def stream_markup(self, camera, now):
        from .mock_frame import render_stream

        return render_stream(camera, now, self.product_shape(camera))

    def capture(self, camera, now):
        from .mock_frame import render_frame

        svg = render_frame(camera, now, self.product_shape(camera))
        return svg.encode("utf-8"), "svg", "image"

    def capture_range(self, camera, start_at, end_at):
        from .mock_frame import render_stream

        # 開始時点から動き続ける映像を保存する。長さはClip.secondsで持つ
        svg = render_stream(camera, start_at, self.product_shape(camera))
        return svg.encode("utf-8"), "svg", "video"

    def export_movie(self, camera, start_at):
        from .mock_movie import render_gif

        return render_gif(camera, start_at, self.product_shape(camera)), "gif"

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

    def stream_markup(self, camera, now):
        raise NotImplementedError(
            "NxWitnessのストリーム再生は未実装です(Issue #25の疎通確認後に対応)。"
        )

    def capture(self, camera, now):
        raise NotImplementedError(
            "NxWitness APIからの映像取得は未実装です(Issue #25の疎通確認後に対応)。"
        )

    def capture_range(self, camera, start_at, end_at):
        raise NotImplementedError(
            "NxWitness APIからの区間切り出しは未実装です(Issue #25の疎通確認後に対応)。"
        )

    def export_movie(self, camera, start_at):
        # 実機は保存したmp4をそのまま渡せるため、変換は不要
        raise NotImplementedError("実機のクリップは保存した動画をそのまま渡します。")


def get_video_source():
    """設定に応じた映像取得元を返す。"""
    if settings.VIDEO_SOURCE == "nx":
        return NxVideoSource()
    return MockVideoSource()
