from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import ListView

from cameras.models import Server


class DashboardView(LoginRequiredMixin, ListView):
    """ログイン後のダッシュボード。カメラ列(サーバー)を選ぶ入り口。

    複数アプリの情報を集約する画面のため、pagesアプリに置いている。
    """

    model = Server
    template_name = "home.html"
    context_object_name = "servers"

    def get_queryset(self):
        # カメラ台数をSQL側で数え、テンプレートでのN+1を避ける
        return Server.objects.annotate(camera_count=Count("cameras"))
