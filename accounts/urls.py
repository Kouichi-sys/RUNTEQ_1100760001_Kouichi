from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # トップページ("/")がログイン画面を兼ねる
    path("", views.UserLoginView.as_view(), name="login"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
]
