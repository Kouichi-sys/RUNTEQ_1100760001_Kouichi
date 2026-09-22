from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import DetailView

from .mock_frame import render_frame
from .models import Camera, Server
from .video_sources import MockVideoSource, get_video_source


class ServerDetailView(LoginRequiredMixin, DetailView):
    """選択されたカメラ列(サーバー)に接続されたカメラの一覧。"""

    model = Server
    template_name = "cameras/server_detail.html"
    context_object_name = "server"

    def get_queryset(self):
        # カメラをまとめて取得し、一覧表示でのN+1を避ける
        return Server.objects.prefetch_related("cameras")


class CameraViewerMixin:
    """映像を再生する画面の共通処理。ライブと過去映像で同じ仕組みを使う。"""

    model = Camera
    context_object_name = "camera"

    def get_queryset(self):
        return Camera.objects.select_related("server")

    def viewer_context(self, start_at):
        """指定した時刻から再生する映像をコンテキストに詰める。"""
        source = get_video_source()
        context = {"source_available": source.is_available()}
        if context["source_available"]:
            context["stream_markup"] = source.stream_markup(self.object, start_at)
            # 映像に重ねて出す時計の開始時刻。一時停止した位置の特定にも使う
            context["started_at"] = start_at.isoformat()
        return context


class CameraLiveView(CameraViewerMixin, LoginRequiredMixin, DetailView):
    """カメラ1台のライブ映像。"""

    template_name = "cameras/camera_live.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.viewer_context(timezone.localtime()))
        return context


class PlaybackView(CameraViewerMixin, LoginRequiredMixin, DetailView):
    """過去映像の再生。日時を指定してその時点から再生する。

    実機(VIDEO_SOURCE=nx)では、再生できる範囲はNxWitness側の録画保持期間に
    依存する。mockでは過去のどの時刻でも再生できる。
    """

    template_name = "cameras/playback.html"
    # 日時を指定しなかったときに、どれだけ遡るか
    DEFAULT_MINUTES_AGO = 60
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M"
    SHORTCUTS = [
        (10, "10分前"),
        (60, "1時間前"),
        (180, "3時間前"),
        (1440, "昨日の今ごろ"),
    ]

    def parse_start_at(self, now):
        """カレンダーで選ばれた日付と時刻を読む。

        未来や読み取れない値は既定値に戻し、理由を画面に出す。
        """
        raw_date = self.request.GET.get("date", "").strip()
        raw_time = self.request.GET.get("time", "").strip()
        default = now - timedelta(minutes=self.DEFAULT_MINUTES_AGO)

        if not raw_date and not raw_time:
            return default, None

        # 片方だけ選ばれたときは、もう片方を既定値で補う
        raw_date = raw_date or default.strftime(self.DATE_FORMAT)
        raw_time = raw_time or default.strftime(self.TIME_FORMAT)

        try:
            parsed = timezone.make_aware(
                datetime.strptime(
                    f"{raw_date} {raw_time}",
                    f"{self.DATE_FORMAT} {self.TIME_FORMAT}",
                )
            )
        except ValueError:
            return default, "日時を読み取れませんでした。既定の1時間前から再生します。"

        if parsed > now:
            return now, "未来の日時は指定できません。現在の映像を表示します。"
        return parsed, None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.localtime()
        start_at, error = self.parse_start_at(now)

        context.update(self.viewer_context(start_at))
        context["error"] = error
        context["date_value"] = start_at.strftime(self.DATE_FORMAT)
        context["time_value"] = start_at.strftime(self.TIME_FORMAT)
        context["max_date"] = now.strftime(self.DATE_FORMAT)
        context["start_at"] = start_at
        context["shortcuts"] = [
            {
                "label": label,
                "date": (now - timedelta(minutes=minutes)).strftime(self.DATE_FORMAT),
                "time": (now - timedelta(minutes=minutes)).strftime(self.TIME_FORMAT),
            }
            for minutes, label in self.SHORTCUTS
        ]
        return context


class StreamView(LoginRequiredMixin, View):
    """指定した時刻から始まる映像を返す。

    巻き戻し・早送りで再生位置が変わったとき、画面側がこれを取得して
    映像を差し替える。
    """

    def get(self, request, pk):
        source = get_video_source()
        camera = get_object_or_404(Camera.objects.select_related("server"), pk=pk)
        at = parse_datetime(request.GET.get("at", "")) or timezone.now()

        markup = source.stream_markup(camera, timezone.localtime(at))
        response = HttpResponse(markup, content_type="image/svg+xml")
        response["Cache-Control"] = "no-store, max-age=0"
        return response


class LiveImageView(LoginRequiredMixin, View):
    """疑似ライブ映像(SVG)を返す。

    VIDEO_SOURCE=mock のときだけ使う。取得のたびに時刻と製品の位置が変わるため、
    一定間隔で読み直すとラインが流れて見える。
    """

    def get(self, request, pk):
        source = get_video_source()
        if not isinstance(source, MockVideoSource):
            raise Http404("疑似映像はVIDEO_SOURCE=mockのときだけ利用できます。")

        camera = get_object_or_404(Camera.objects.select_related("server"), pk=pk)
        # 動画を一時停止した位置のコマが欲しい場合はatで指定する
        at = parse_datetime(request.GET.get("at", "")) or timezone.now()
        svg = render_frame(
            camera, timezone.localtime(at), source.product_shape(camera)
        )

        response = HttpResponse(svg, content_type="image/svg+xml")
        # 常に最新のコマを返したいのでキャッシュさせない
        response["Cache-Control"] = "no-store, max-age=0"
        return response
