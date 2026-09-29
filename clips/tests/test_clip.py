import os
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from accounts.factories import UserFactory
from cameras.factories import CameraFactory
from clips.models import Clip
from clips.tests.base import MediaTestCase


class ClipCreateTests(MediaTestCase):
    """開始と終了を指定して、区間をクリップとして保存する。"""

    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.base_url = reverse("clips:clip", args=[self.camera.pk])
        self.client.force_login(self.user)
        self.now = timezone.now()

    def url_for(self, start_delta, end_delta):
        """いまを基準に、開始・終了を指定したURLを組み立てる。"""
        query = urlencode({
            "start": (self.now + start_delta).isoformat(),
            "end": (self.now + end_delta).isoformat(),
        })
        return f"{self.base_url}?{query}"

    def test_保存フォームを開ける(self):
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "クリップの保存")
        self.assertContains(response, "60 秒")

    def test_保存できる(self):
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        response = self.client.post(url, {"title": "詰まりから復旧まで", "memo": "手動復帰"})

        self.assertEqual(response.status_code, 302)
        clip = Clip.objects.get()
        self.assertEqual(clip.title, "詰まりから復旧まで")
        self.assertEqual(clip.user, self.user)
        self.assertEqual(clip.camera, self.camera)

    def test_クリップとして保存される(self):
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        self.client.post(url, {"title": "復旧まで", "memo": ""})

        clip = Clip.objects.get()
        self.assertEqual(clip.media_type, Clip.VIDEO)
        self.assertTrue(clip.is_video)

    def test_長さが記録される(self):
        url = self.url_for(timedelta(minutes=-5), timedelta(seconds=-205))

        self.client.post(url, {"title": "復旧まで", "memo": ""})

        self.assertEqual(Clip.objects.get().seconds, 95)

    def test_開始時刻が撮影日時になる(self):
        start = self.now - timedelta(minutes=5)
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        self.client.post(url, {"title": "復旧まで", "memo": ""})

        self.assertAlmostEqual(
            Clip.objects.get().taken_at, start, delta=timedelta(milliseconds=10)
        )

    def test_実ファイルが作られる(self):
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        self.client.post(url, {"title": "復旧まで", "memo": ""})

        clip = Clip.objects.get()
        path = os.path.join(settings.MEDIA_ROOT, clip.file.name)
        self.assertTrue(os.path.exists(path))

    def test_タイトルが空だと保存されない(self):
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        response = self.client.post(url, {"title": "", "memo": ""})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Clip.objects.exists())

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()
        url = self.url_for(timedelta(minutes=-5), timedelta(minutes=-4))

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)


class ClipRangeValidationTests(MediaTestCase):
    """範囲の指定が正しくないときは、理由を出して保存しない。"""

    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.base_url = reverse("clips:clip", args=[self.camera.pk])
        self.client.force_login(self.user)
        self.now = timezone.now()

    def assert_rejected(self, params, message):
        url = f"{self.base_url}?{urlencode(params)}" if params else self.base_url

        response = self.client.get(url)
        self.assertContains(response, message)

        self.client.post(url, {"title": "保存されないはず", "memo": ""})
        self.assertFalse(Clip.objects.exists())

    def test_範囲の指定がない(self):
        self.assert_rejected({}, "切り取る範囲が指定されていません。")

    def test_終了が開始より前(self):
        self.assert_rejected(
            {
                "start": self.now.isoformat(),
                "end": (self.now - timedelta(minutes=1)).isoformat(),
            },
            "終了は開始より後にしてください。",
        )

    def test_未来の範囲(self):
        self.assert_rejected(
            {
                "start": (self.now + timedelta(minutes=1)).isoformat(),
                "end": (self.now + timedelta(minutes=2)).isoformat(),
            },
            "未来の範囲は指定できません。",
        )

    def test_長すぎる範囲(self):
        self.assert_rejected(
            {
                "start": (self.now - timedelta(minutes=30)).isoformat(),
                "end": self.now.isoformat(),
            },
            "範囲が長すぎます。10分以内にしてください。",
        )

    def test_短すぎる範囲(self):
        self.assert_rejected(
            {
                "start": (self.now - timedelta(seconds=10)).isoformat(),
                "end": (self.now - timedelta(seconds=9, milliseconds=500)).isoformat(),
            },
            "範囲が短すぎます。1秒以上にしてください。",
        )
