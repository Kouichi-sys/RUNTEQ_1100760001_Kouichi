import re
from datetime import timedelta
from urllib.parse import quote, urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from cameras.models import Camera
from cameras.video_sources import get_video_source

from .forms import ClipForm
from .models import Clip


class ScreenshotCreateView(LoginRequiredMixin, CreateView):
    """いま見ている映像の1コマをスクリーンショットとして保存する。

    区間を切り取るクリップ(動画)とは別の機能で、media_typeがimageになる。
    ファイルはMEDIA_ROOT配下に置き、DBにはパスだけを持つ
    (NxWitness側のデータには一切手を加えない)。
    """

    model = Clip
    form_class = ClipForm
    template_name = "clips/screenshot_form.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.camera = get_object_or_404(
            Camera.objects.select_related("server"), pk=kwargs["camera_pk"]
        )

    def captured_at(self):
        """切り出す時刻。動画を一時停止していれば、その瞬間を使う。

        値は画面から送られてくるため、現在時刻から大きく離れていれば無視する。
        """
        raw = self.request.GET.get("at")
        if raw:
            parsed = parse_datetime(raw)
            if parsed and abs(timezone.now() - parsed) < timedelta(minutes=10):
                return parsed
        return timezone.now()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["camera"] = self.camera
        captured_at = self.captured_at()
        context["captured_at"] = timezone.localtime(captured_at)
        source = get_video_source()
        if source.is_available():
            # 保存されるのと同じコマをプレビューに出す
            query = urlencode({"at": captured_at.isoformat()})
            context["preview_url"] = f"{source.live_image_url(self.camera)}?{query}"
        return context

    def form_valid(self, form):
        taken_at = self.captured_at()
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
        messages.success(self.request, f"スクリーンショット「{clip.title}」を保存しました。")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # マイページ(#15)ができるまでは、元のライブ画面に戻す
        return reverse("cameras:camera_live", args=[self.camera.pk])


class ClipCreateView(LoginRequiredMixin, CreateView):
    """過去映像から、開始と終了を指定した区間をクリップとして保存する。

    1コマだけのスクリーンショットとは別で、media_typeがvideoになる。
    """

    model = Clip
    form_class = ClipForm
    template_name = "clips/clip_form.html"

    # 長すぎるクリップは保存に時間がかかり、報告書にも使いにくい
    MAX_SECONDS = 10 * 60
    MIN_SECONDS = 1

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.camera = get_object_or_404(
            Camera.objects.select_related("server"), pk=kwargs["camera_pk"]
        )

    def clip_range(self):
        """指定された区間を読む。不正なら理由を添えて返す。

        戻り値は (開始, 終了, エラー文言)。
        """
        now = timezone.now()
        start = parse_datetime(self.request.GET.get("start", "") or "")
        end = parse_datetime(self.request.GET.get("end", "") or "")

        if not start or not end:
            return None, None, "切り取る範囲が指定されていません。"
        if end <= start:
            return None, None, "終了は開始より後にしてください。"
        if start > now or end > now:
            return None, None, "未来の範囲は指定できません。"

        seconds = (end - start).total_seconds()
        if seconds < self.MIN_SECONDS:
            return None, None, "範囲が短すぎます。1秒以上にしてください。"
        if seconds > self.MAX_SECONDS:
            return None, None, "範囲が長すぎます。10分以内にしてください。"

        return start, end, None

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

        source = get_video_source()
        if source.is_available():
            # 切り取りの開始時点をプレビューに出す
            query = urlencode({"at": start.isoformat()})
            context["preview_url"] = f"{source.live_image_url(self.camera)}?{query}"
        return context

    def form_valid(self, form):
        start, end, error = self.clip_range()
        if error:
            form.add_error(None, error)
            return self.form_invalid(form)

        content, extension, media_type = get_video_source().capture_range(
            self.camera, timezone.localtime(start), timezone.localtime(end)
        )

        clip = form.save(commit=False)
        clip.user = self.request.user
        clip.camera = self.camera
        clip.taken_at = start
        clip.seconds = int((end - start).total_seconds())
        clip.media_type = media_type
        clip.file.save(f"clip.{extension}", ContentFile(content), save=False)
        clip.save()

        self.object = clip
        messages.success(self.request, f"クリップ「{clip.title}」を保存しました。")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # マイページ(#15)ができるまでは、元の過去映像画面に戻す
        return reverse("cameras:playback", args=[self.camera.pk])


class MyPageView(LoginRequiredMixin, ListView):
    """自分が保存したクリップとスクリーンショットの一覧。

    保存したデータは本人だけが見られる(README 7章の方針)。
    """

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
        mine = Clip.objects.filter(user=self.request.user)
        context["selected_type"] = self.request.GET.get("type", "")
        context["total_count"] = mine.count()
        context["image_count"] = mine.filter(media_type=Clip.IMAGE).count()
        context["video_count"] = mine.filter(media_type=Clip.VIDEO).count()
        return context


class ClipFileView(LoginRequiredMixin, View):
    """保存したファイルを返す。

    MEDIA_ROOTを直接公開すると、URLを知っていれば誰でも見られてしまう。
    保存した本人かどうかを確かめてから返す。
    社内NASに置いた場合も同じ経路で配信できる。
    """

    def get(self, request, pk):
        clip = get_object_or_404(Clip, pk=pk, user=request.user)
        if not clip.file or not clip.file.storage.exists(clip.file.name):
            raise Http404("ファイルが見つかりません。")

        content_type = "image/svg+xml" if clip.file.name.endswith(".svg") else None
        return FileResponse(clip.file.open("rb"), content_type=content_type)


class ClipDetailView(LoginRequiredMixin, DetailView):
    """保存した1件の詳細。映像・メモ・撮影元を確認できる。

    保存した本人だけが開ける。他人のものは存在ごと隠す(404)。
    """

    model = Clip
    template_name = "clips/clip_detail.html"
    context_object_name = "clip"

    def get_queryset(self):
        return Clip.objects.filter(user=self.request.user).select_related(
            "camera", "camera__server"
        )


class ClipThumbnailView(LoginRequiredMixin, View):
    """一覧に並べるための静止画を返す。

    クリップ(動画)をそのまま一覧に並べると、開いた枚数だけ映像が動き続けて
    画面が重くなる。一覧では動きを止めた絵を返し、詳細画面でだけ再生する。

    mockの映像はSVGなので、アニメーションの指定を外すだけで静止画になる。
    実機の動画(mp4など)に切り替えるときは、NxWitnessのサムネイルを使う。
    """

    # 生成したSVGのアニメーション定義。これを外すと最初のコマで止まる
    STYLE_PATTERN = re.compile(r"<style>.*?</style>", re.DOTALL)

    def get(self, request, pk):
        clip = get_object_or_404(Clip, pk=pk, user=request.user)
        if not clip.file or not clip.file.storage.exists(clip.file.name):
            raise Http404("ファイルが見つかりません。")

        # 静止画はそのまま返す
        if not clip.is_video or not clip.file.name.endswith(".svg"):
            return FileResponse(clip.file.open("rb"), content_type="image/svg+xml")

        with clip.file.open("rb") as stored:
            svg = stored.read().decode("utf-8")
        return HttpResponse(
            self.STYLE_PATTERN.sub("", svg), content_type="image/svg+xml"
        )


class ClipDownloadView(LoginRequiredMixin, View):
    """保存したファイルをPCにダウンロードさせる。

    閲覧用(ClipFileView)と同じく、保存した本人だけが取得できる。
    報告書に添付できるよう、中身が分かるファイル名を付ける。
    """

    def get(self, request, pk):
        clip = get_object_or_404(
            Clip.objects.select_related("camera", "camera__server"),
            pk=pk,
            user=request.user,
        )
        if not clip.file or not clip.file.storage.exists(clip.file.name):
            raise Http404("ファイルが見つかりません。")

        # mockの保存形式(SVG)はメールで配りにくいため、動くGIFに直して渡す。
        # 実機のクリップ(mp4)は変換せずそのまま渡す。
        if clip.is_video and clip.file.name.endswith(".svg"):
            content, extension = get_video_source().export_movie(
                clip.camera, timezone.localtime(clip.taken_at)
            )
            response = HttpResponse(content, content_type="image/gif")
            response["Content-Disposition"] = (
                f"attachment; filename*=UTF-8''{quote(clip.movie_name(extension))}"
            )
            return response

        return FileResponse(
            clip.file.open("rb"),
            as_attachment=True,
            filename=clip.download_name,
        )


class ClipUpdateView(LoginRequiredMixin, UpdateView):
    """保存したもののタイトル・メモを直す。

    映像そのものは差し替えない。トラブル対応中に走り書きしたメモを、
    落ち着いてから報告書向けに書き直す使い方を想定している。
    保存した本人だけが開ける。
    """

    model = Clip
    form_class = ClipForm
    template_name = "clips/clip_edit.html"

    def get_queryset(self):
        # 他人のものは編集画面ごと開けない
        return Clip.objects.filter(user=self.request.user).select_related(
            "camera", "camera__server"
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"「{self.object.title}」を更新しました。")
        return response

    def get_success_url(self):
        return reverse("clips:detail", args=[self.object.pk])
