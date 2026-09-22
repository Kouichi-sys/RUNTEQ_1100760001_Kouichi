from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView

from cameras.models import Camera
from cameras.video_sources import get_video_source

from .forms import ClipForm
from .models import Clip


class ClipCreateView(LoginRequiredMixin, CreateView):
    """いま見ている映像をクリップとして保存する。

    映像の実体は保存操作をした時点で切り出す。ファイルはMEDIA_ROOT配下に置き、
    DBにはパスだけを持つ(NxWitness側のデータには一切手を加えない)。
    """

    model = Clip
    form_class = ClipForm
    template_name = "clips/clip_form.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.camera = get_object_or_404(
            Camera.objects.select_related("server"), pk=kwargs["camera_pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["camera"] = self.camera
        source = get_video_source()
        if source.is_available():
            context["live_image_url"] = source.live_image_url(self.camera)
        return context

    def form_valid(self, form):
        taken_at = timezone.now()
        content, extension, media_type = get_video_source().capture(
            self.camera, timezone.localtime(taken_at)
        )

        clip = form.save(commit=False)
        clip.user = self.request.user
        clip.camera = self.camera
        clip.taken_at = taken_at
        clip.media_type = media_type
        # taken_at を使って保存先を決めるため、ファイルは属性を入れてから渡す
        clip.file.save(f"clip.{extension}", ContentFile(content), save=False)
        clip.save()

        self.object = clip
        messages.success(self.request, f"「{clip.title}」を保存しました。")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # マイページ(#15)ができるまでは、元のライブ画面に戻す
        return reverse("cameras:camera_live", args=[self.camera.pk])
