from django.urls import path

from . import views

app_name = "cameras"

urlpatterns = [
    path("servers/<int:pk>/", views.ServerDetailView.as_view(), name="server_detail"),
    path("cameras/<int:pk>/", views.CameraLiveView.as_view(), name="camera_live"),
    path("cameras/<int:pk>/playback/", views.PlaybackView.as_view(), name="playback"),
    # 再生位置を変えたときに映像を差し替えるための取得先
    path("cameras/<int:pk>/stream.svg", views.StreamView.as_view(), name="stream"),
    # 一覧のサムネイルと、クリップに保存する1コマ
    path("cameras/<int:pk>/live.svg", views.LiveImageView.as_view(), name="live_image"),
]
