from django.urls import path

from . import views

app_name = "clips"

urlpatterns = [
    path(
        "cameras/<int:camera_pk>/screenshot/",
        views.ScreenshotCreateView.as_view(),
        name="screenshot",
    ),
]
