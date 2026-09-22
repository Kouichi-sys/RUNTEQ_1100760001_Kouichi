from django.urls import path

from . import views

app_name = "clips"

urlpatterns = [
    path(
        "cameras/<int:camera_pk>/clip/",
        views.ClipCreateView.as_view(),
        name="create",
    ),
]
