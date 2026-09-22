from django.urls import path

from . import views

app_name = "clips"

urlpatterns = [
    path("mypage/", views.MyPageView.as_view(), name="mypage"),
    path("clips/<int:pk>/", views.ClipDetailView.as_view(), name="detail"),
    path("clips/<int:pk>/file/", views.ClipFileView.as_view(), name="file"),
    path("clips/<int:pk>/thumbnail.svg", views.ClipThumbnailView.as_view(), name="thumbnail"),
    path(
        "cameras/<int:camera_pk>/screenshot/",
        views.ScreenshotCreateView.as_view(),
        name="screenshot",
    ),
    path(
        "cameras/<int:camera_pk>/clip/",
        views.ClipCreateView.as_view(),
        name="clip",
    ),
]
