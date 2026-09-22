from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import LoginForm, SignupForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    # 既にログイン済みならトップへ戻す
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    pass


class SignupView(CreateView):
    """社内アカウントの新規登録。登録後はそのままログインした状態にする。"""

    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("pages:home")

    def dispatch(self, request, *args, **kwargs):
        # ログイン済みのユーザーに登録画面を見せる意味がないため戻す
        if request.user.is_authenticated:
            return redirect("pages:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
