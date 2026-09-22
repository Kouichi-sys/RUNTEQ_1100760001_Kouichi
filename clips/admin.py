from django.contrib import admin

from .models import Clip


@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "camera", "media_type", "taken_at")
    list_filter = ("media_type", "camera__server")
    search_fields = ("title", "memo", "user__email")
    date_hierarchy = "taken_at"

    def get_queryset(self, request):
        # 一覧でユーザー名・カメラ名を出すため、先に結合しておく
        return super().get_queryset(request).select_related("user", "camera")
