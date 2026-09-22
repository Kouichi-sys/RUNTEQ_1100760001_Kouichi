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


class CameraLiveView(LoginRequiredMixin, DetailView):
    """カメラ1台のライブ映像。"""

    model = Camera
    template_name = "cameras/camera_live.html"
    context_object_name = "camera"

    def get_queryset(self):
        return Camera.objects.select_related("server")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        source = get_video_source()
        context["source_available"] = source.is_available()
        if context["source_available"]:
            now = timezone.localtime()
            context["stream_markup"] = source.stream_markup(self.object, now)
            # 映像に重ねて出す時計の開始時刻。一時停止した位置の特定にも使う
            context["started_at"] = now.isoformat()
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
