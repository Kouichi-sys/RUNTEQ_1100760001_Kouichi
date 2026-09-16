from django.contrib.auth.views import LoginView, LogoutView

from .forms import LoginForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    # 既にログイン済みならトップへ戻す
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    pass
