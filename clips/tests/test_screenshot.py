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


class ScreenshotCreateTests(MediaTestCase):
    """表示中の1コマをスクリーンショットとして保存する。"""

    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.url = reverse("clips:screenshot", args=[self.camera.pk])
        self.client.force_login(self.user)

    def test_保存フォームを開ける(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "スクリーンショットの保存")

    def test_保存できる(self):
        response = self.client.post(self.url, {"title": "充填部の詰まり", "memo": "缶が横倒し"})

        self.assertEqual(response.status_code, 302)
        clip = Clip.objects.get()
        self.assertEqual(clip.title, "充填部の詰まり")
        self.assertEqual(clip.memo, "缶が横倒し")
        self.assertEqual(clip.user, self.user)
        self.assertEqual(clip.camera, self.camera)

    def test_スクリーンショットとして保存される(self):
        self.client.post(self.url, {"title": "詰まり", "memo": ""})

        clip = Clip.objects.get()
        self.assertEqual(clip.media_type, Clip.IMAGE)
        self.assertEqual(clip.seconds, 0)
        self.assertFalse(clip.is_video)

    def test_実ファイルが作られる(self):
        self.client.post(self.url, {"title": "詰まり", "memo": ""})

        clip = Clip.objects.get()
        path = os.path.join(settings.MEDIA_ROOT, clip.file.name)
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_保存先は日本時間の日付で分かれる(self):
        self.client.post(self.url, {"title": "詰まり", "memo": ""})

        clip = Clip.objects.get()
        taken = timezone.localtime(clip.taken_at)
        self.assertIn(taken.strftime("%Y/%m/%d"), clip.file.name)

    def test_一時停止した時刻を指定して保存できる(self):
        at = timezone.now() - timedelta(seconds=30)

        self.client.post(
            f"{self.url}?{urlencode({'at': at.isoformat()})}", {"title": "詰まり", "memo": ""}
        )

        clip = Clip.objects.get()
        self.assertAlmostEqual(clip.taken_at, at, delta=timedelta(milliseconds=10))

    def test_かけ離れた時刻の指定は現在時刻に丸める(self):
        at = timezone.now() - timedelta(days=3)

        self.client.post(
            f"{self.url}?{urlencode({'at': at.isoformat()})}", {"title": "詰まり", "memo": ""}
        )

        clip = Clip.objects.get()
        self.assertLess((timezone.now() - clip.taken_at).total_seconds(), 60)

    def test_タイトルが空だと保存されない(self):
        response = self.client.post(self.url, {"title": "", "memo": "メモだけ"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Clip.objects.exists())

    def test_メモは省略できる(self):
        self.client.post(self.url, {"title": "詰まり", "memo": ""})

        self.assertEqual(Clip.objects.get().memo, "")

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Clip.objects.exists())

    def test_存在しないカメラでは保存できない(self):
        response = self.client.get(reverse("clips:screenshot", args=[9999]))

        self.assertEqual(response.status_code, 404)
