from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from .models import Server


class ServerDetailView(LoginRequiredMixin, DetailView):
    """選択されたカメラ列(サーバー)に接続されたカメラの一覧。"""

    model = Server
    template_name = "cameras/server_detail.html"
    context_object_name = "server"

    def get_queryset(self):
        # カメラをまとめて取得し、一覧表示でのN+1を避ける
        return Server.objects.prefetch_related("cameras")
