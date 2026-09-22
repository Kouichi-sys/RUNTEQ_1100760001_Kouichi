from django.urls import path

from . import views

app_name = "cameras"

urlpatterns = [
    path("servers/<int:pk>/", views.ServerDetailView.as_view(), name="server_detail"),
    path("cameras/<int:pk>/", views.CameraLiveView.as_view(), name="camera_live"),
    # ライブ映像の取得先。<img>から一定間隔で読み直す
    path("cameras/<int:pk>/live.svg", views.LiveImageView.as_view(), name="live_image"),
]
