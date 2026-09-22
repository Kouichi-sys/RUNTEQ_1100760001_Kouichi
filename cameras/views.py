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
    INPUT_FORMAT = "%Y-%m-%dT%H:%M"
    SHORTCUTS = [
        (10, "10分前"),
        (60, "1時間前"),
        (180, "3時間前"),
        (1440, "24時間前"),
    ]

    def parse_start_at(self, now):
        """入力された日時を読む。未来や読めない値は既定値に戻す。"""
        raw = self.request.GET.get("at", "").strip()
        if not raw:
            return now - timedelta(minutes=self.DEFAULT_MINUTES_AGO), None

        try:
            parsed = timezone.make_aware(datetime.strptime(raw, self.INPUT_FORMAT))
        except ValueError:
            return (
                now - timedelta(minutes=self.DEFAULT_MINUTES_AGO),
                "日時を読み取れませんでした。既定の1時間前から再生します。",
            )

        if parsed > now:
            return now, "未来の日時は指定できません。現在の映像を表示します。"
        return parsed, None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.localtime()
        start_at, error = self.parse_start_at(now)

        context.update(self.viewer_context(start_at))
        context["error"] = error
        context["form_value"] = start_at.strftime(self.INPUT_FORMAT)
        context["max_value"] = now.strftime(self.INPUT_FORMAT)
        context["shortcuts"] = [
            {
                "label": label,
                "value": (now - timedelta(minutes=minutes)).strftime(self.INPUT_FORMAT),
            }
            for minutes, label in self.SHORTCUTS
        ]
        return context


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
