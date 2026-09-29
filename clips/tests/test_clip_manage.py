import os

from django.conf import settings
from django.urls import reverse

from accounts.factories import UserFactory
from clips.factories import ClipFactory
from clips.models import Clip
from clips.tests.base import MediaTestCase


class ClipDetailTests(MediaTestCase):
    """保存した1件の詳細。本人以外には存在ごと隠す。"""

    def setUp(self):
        self.user = UserFactory()
        self.other = UserFactory()
        self.clip = ClipFactory(user=self.user, title="詰まりの様子", memo="缶が横倒し")

    def test_本人は詳細を見られる(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("clips:detail", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "詰まりの様子")
        self.assertContains(response, "缶が横倒し")

    def test_他人は見られない(self):
        self.client.force_login(self.other)

        response = self.client.get(reverse("clips:detail", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 404)

    def test_未ログインでは見られない(self):
        response = self.client.get(reverse("clips:detail", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 302)

    def test_クリップは長さを表示する(self):
        self.client.force_login(self.user)
        clip = ClipFactory(user=self.user, video=True)

        response = self.client.get(reverse("clips:detail", args=[clip.pk]))

        self.assertContains(response, "60 秒")


class ClipUpdateTests(MediaTestCase):
    """タイトルとメモだけを直せる。映像は差し替えない。"""

    def setUp(self):
        self.user = UserFactory()
        self.other = UserFactory()
        self.clip = ClipFactory(user=self.user, title="走り書き", memo="あとで直す")
        self.url = reverse("clips:edit", args=[self.clip.pk])

    def test_本人は編集できる(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"title": "缶詰まり", "memo": "手動復帰"})

        self.assertEqual(response.status_code, 302)
        self.clip.refresh_from_db()
        self.assertEqual(self.clip.title, "缶詰まり")
        self.assertEqual(self.clip.memo, "手動復帰")

    def test_映像と撮影日時は変わらない(self):
        self.client.force_login(self.user)
        before_file = self.clip.file.name
        before_taken = self.clip.taken_at

        self.client.post(self.url, {"title": "缶詰まり", "memo": ""})

        self.clip.refresh_from_db()
        self.assertEqual(self.clip.file.name, before_file)
        self.assertEqual(self.clip.taken_at, before_taken)

    def test_タイトルが空だと更新されない(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"title": "", "memo": "メモだけ"})

        self.assertEqual(response.status_code, 200)
        self.clip.refresh_from_db()
        self.assertEqual(self.clip.title, "走り書き")

    def test_他人は編集画面を開けない(self):
        self.client.force_login(self.other)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_他人は書き換えられない(self):
        self.client.force_login(self.other)

        response = self.client.post(self.url, {"title": "乗っ取り", "memo": ""})

        self.assertEqual(response.status_code, 404)
        self.clip.refresh_from_db()
        self.assertEqual(self.clip.title, "走り書き")


class ClipDeleteTests(MediaTestCase):
    """削除は本人のみ。実ファイルも一緒に消す。"""

    def setUp(self):
        self.user = UserFactory()
        self.other = UserFactory()
        self.clip = ClipFactory(user=self.user, title="消す予定")
        self.url = reverse("clips:delete", args=[self.clip.pk])
        self.path = os.path.join(settings.MEDIA_ROOT, self.clip.file.name)

    def test_確認画面を開いただけでは消えない(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "元に戻せません")
        self.assertTrue(Clip.objects.filter(pk=self.clip.pk).exists())

    def test_本人は削除できる(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Clip.objects.filter(pk=self.clip.pk).exists())

    def test_実ファイルも消える(self):
        self.client.force_login(self.user)
        self.assertTrue(os.path.exists(self.path))

        self.client.post(self.url)

        self.assertFalse(os.path.exists(self.path))

    def test_他人は削除できない(self):
        self.client.force_login(self.other)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Clip.objects.filter(pk=self.clip.pk).exists())

    def test_他人のぶんを消しても他に影響しない(self):
        mine = ClipFactory(user=self.user)
        self.client.force_login(self.user)

        self.client.post(self.url)

        self.assertTrue(Clip.objects.filter(pk=mine.pk).exists())

    def test_未ログインでは削除できない(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Clip.objects.filter(pk=self.clip.pk).exists())
