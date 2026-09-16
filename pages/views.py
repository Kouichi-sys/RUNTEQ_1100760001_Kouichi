from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    """ログイン後のホーム。各機能への入り口をまとめる。

    カメラ列の選択を含むダッシュボードは Issue #9 でここを置き換える。
    """

    template_name = "home.html"
