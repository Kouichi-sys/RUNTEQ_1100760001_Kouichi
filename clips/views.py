from urllib.parse import quote, urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from cameras.models import Camera
from cameras.video_sources import get_video_source

from . import services
from .forms import ClipForm
from .models import Clip


class OwnClipMixin(LoginRequiredMixin):
    """保存した本人のものだけを扱う。他人のものは存在ごと隠す(404)。"""

    def get_queryset(self):
        return Clip.objects.filter(user=self.request.user).select_related(
            "camera", "camera__server"
        )

    def get_clip(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)


class CameraCaptureMixin(LoginRequiredMixin):
    """カメラを選んで保存する画面の共通処理。"""

    model = Clip
    form_class = ClipForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.camera = get_object_or_404(
            Camera.objects.select_related("server"), pk=kwargs["camera_pk"]
        )

    def preview_url(self, at):
        """保存されるのと同じコマをプレビューに出す。"""
        source = get_video_source()
        if not source.is_available():
            return None
        query = urlencode({"at": at.isoformat()})
        return f"{source.live_image_url(self.camera)}?{query}"

    def saved(self, clip, label):
        self.object = clip
        messages.success(self.request, f"{label}「{clip.title}」を保存しました。")
        return HttpResponseRedirect(self.get_success_url())


class ScreenshotCreateView(CameraCaptureMixin, CreateView):
    """いま見ている映像の1コマをスクリーンショットとして保存する。

    区間を切り取るクリップとは別の機能で、media_typeがimageになる。
    """

    template_name = "clips/screenshot_form.html"

    def captured_at(self):
        return services.resolve_capture_time(self.request.GET.get("at"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        captured_at = self.captured_at()
        context["camera"] = self.camera
        context["captured_at"] = timezone.localtime(captured_at)
        context["preview_url"] = self.preview_url(captured_at)
        return context

    def form_valid(self, form):
        clip = services.save_screenshot(
            user=self.request.user,
            camera=self.camera,
            taken_at=self.captured_at(),
            title=form.cleaned_data["title"],
            memo=form.cleaned_data["memo"],
        )
        return self.saved(clip, "スクリーンショット")

    def get_success_url(self):
        return reverse("cameras:camera_live", args=[self.camera.pk])


class ClipCreateView(CameraCaptureMixin, CreateView):
    """過去映像から、開始と終了を指定した区間をクリップとして保存する。"""

    template_name = "clips/clip_form.html"

    def clip_range(self):
        return services.resolve_clip_range(
            self.request.GET.get("start"), self.request.GET.get("end")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end, error = self.clip_range()
        context["camera"] = self.camera
        context["error"] = error
        if error:
            return context

        context["start_at"] = timezone.localtime(start)
        context["end_at"] = timezone.localtime(end)
        context["seconds"] = int((end - start).total_seconds())
        context["preview_url"] = self.preview_url(start)
        return context

    def form_valid(self, form):
        start, end, error = self.clip_range()
        if error:
            form.add_error(None, error)
            return self.form_invalid(form)

        clip = services.save_clip(
            user=self.request.user,
            camera=self.camera,
            start_at=start,
            end_at=end,
            title=form.cleaned_data["title"],
            memo=form.cleaned_data["memo"],
        )
        return self.saved(clip, "クリップ")

    def get_success_url(self):
        return reverse("cameras:playback", args=[self.camera.pk])


class MyPageView(LoginRequiredMixin, ListView):
    """自分が保存したクリップとスクリーンショットの一覧。"""

    model = Clip
    template_name = "clips/mypage.html"
    context_object_name = "clips"
    paginate_by = 12

    def get_queryset(self):
        # 他人のクリップは一切出さない
        queryset = Clip.objects.filter(user=self.request.user).select_related(
            "camera", "camera__server"
        )
        media_type = self.request.GET.get("type")
        if media_type in (Clip.IMAGE, Clip.VIDEO):
            queryset = queryset.filter(media_type=media_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 種別ごとに数えると問い合わせが3回になるため、1回で数える
        counts = Clip.objects.filter(user=self.request.user).aggregate(
            total=Count("pk"),
            image=Count("pk", filter=Q(media_type=Clip.IMAGE)),
            video=Count("pk", filter=Q(media_type=Clip.VIDEO)),
        )
        context["selected_type"] = self.request.GET.get("type", "")
        context["total_count"] = counts["total"]
        context["image_count"] = counts["image"]
        context["video_count"] = counts["video"]
        return context


class ClipDetailView(OwnClipMixin, DetailView):
    """保存した1件の詳細。映像・メモ・撮影元を確認できる。"""

    model = Clip
    template_name = "clips/clip_detail.html"
    context_object_name = "clip"


class ClipUpdateView(OwnClipMixin, UpdateView):
    """タイトル・メモを直す。映像そのものは差し替えない。"""

    model = Clip
    form_class = ClipForm
    template_name = "clips/clip_edit.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"「{self.object.title}」を更新しました。")
        return response

    def get_success_url(self):
        return reverse("clips:detail", args=[self.object.pk])


class ClipDeleteView(OwnClipMixin, DeleteView):
    """保存したものを削除する。取り消せないため確認画面をはさむ。"""

    model = Clip
    template_name = "clips/clip_confirm_delete.html"
    success_url = reverse_lazy("clips:mypage")

    def form_valid(self, form):
        title = self.object.title
        # DBの行だけ消すと、保存先(NAS)に実ファイルが残ってしまう
        self.object.file.delete(save=False)
        response = super().form_valid(form)
        messages.success(self.request, f"「{title}」を削除しました。")
        return response


class StoredFileView(OwnClipMixin, View):
    """保存したファイルを扱うビューの共通部分。"""

    def get_stored_clip(self, pk):
        clip = self.get_clip(pk)
        if not clip.file or not clip.file.storage.exists(clip.file.name):
            raise Http404("ファイルが見つかりません。")
        return clip


class ClipFileView(StoredFileView):
    """画面に表示するためにファイルを返す。

    MEDIA_ROOTを直接公開するとURLを知っていれば誰でも見られてしまうため、
    保存した本人かどうかを確かめてから返す。社内NASに置いても同じ経路で配信できる。
    """

    def get(self, request, pk):
        clip = self.get_stored_clip(pk)
        content_type = "image/svg+xml" if clip.file.name.endswith(".svg") else None
        return FileResponse(clip.file.open("rb"), content_type=content_type)


class ClipThumbnailView(StoredFileView):
    """一覧に並べるための静止画を返す。"""

    def get(self, request, pk):
        clip = self.get_stored_clip(pk)
        if not services.needs_still_conversion(clip):
            return FileResponse(clip.file.open("rb"), content_type="image/svg+xml")
        return HttpResponse(services.still_image(clip), content_type="image/svg+xml")


class ClipDownloadView(StoredFileView):
    """PCにダウンロードさせる。報告書に添付できるファイル名を付ける。"""

    def get(self, request, pk):
        clip = self.get_stored_clip(pk)

        if services.needs_movie_conversion(clip):
            content, filename = services.shareable_movie(clip)
            response = HttpResponse(content, content_type="image/gif")
            response["Content-Disposition"] = (
                f"attachment; filename*=UTF-8''{quote(filename)}"
            )
            return response

        return FileResponse(
            clip.file.open("rb"), as_attachment=True, filename=clip.download_name
        )
