from django.urls import path

from . import views

app_name = "cameras"

urlpatterns = [
    path("<int:pk>/", views.ServerDetailView.as_view(), name="server_detail"),
]
