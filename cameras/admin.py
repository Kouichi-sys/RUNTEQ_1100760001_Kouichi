from django.contrib import admin

from .models import Camera, Server


class CameraInline(admin.TabularInline):
    """サーバーの編集画面から、ぶら下がるカメラをまとめて登録できるようにする。"""

    model = Camera
    extra = 1


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "line", "address")
    search_fields = ("name", "line", "address")
    inlines = (CameraInline,)


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("name", "server")
    list_filter = ("server",)
    search_fields = ("name", "server__name")

    def get_queryset(self, request):
        # 一覧でサーバー名を出すため、N+1を避けて先に結合しておく
        return super().get_queryset(request).select_related("server")
