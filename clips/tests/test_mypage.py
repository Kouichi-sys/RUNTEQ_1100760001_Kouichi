from django.urls import reverse

from accounts.factories import UserFactory
from clips.factories import ClipFactory
from clips.models import Clip
from clips.tests.base import MediaTestCase


class MyPageTests(MediaTestCase):
    """マイページには自分が保存したものだけを出す。"""

    def setUp(self):
        self.user = UserFactory()
        self.other = UserFactory()
        self.url = reverse("clips:mypage")
        self.client.force_login(self.user)

    def test_自分のクリップが表示される(self):
        clip = ClipFactory(user=self.user, title="自分のクリップ")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, clip.title)

    def test_他人のクリップは表示されない(self):
        ClipFactory(user=self.other, title="他人のクリップ")

        response = self.client.get(self.url)

        self.assertNotContains(response, "他人のクリップ")
        self.assertEqual(list(response.context["clips"]), [])

    def test_自分のものだけが並ぶ(self):
        mine = ClipFactory.create_batch(2, user=self.user)
        ClipFactory.create_batch(3, user=self.other)

        response = self.client.get(self.url)

        self.assertEqual(
            {clip.pk for clip in response.context["clips"]},
            {clip.pk for clip in mine},
        )

    def test_新しいものが先に並ぶ(self):
        old = ClipFactory(user=self.user)
        new = ClipFactory(user=self.user)
        Clip.objects.filter(pk=old.pk).update(taken_at=old.taken_at.replace(year=2020))

        clips = list(self.client.get(self.url).context["clips"])

        self.assertEqual(clips[0].pk, new.pk)

    def test_種別で絞り込める(self):
        shot = ClipFactory(user=self.user)
        clip = ClipFactory(user=self.user, video=True)

        videos = self.client.get(f"{self.url}?type=video").context["clips"]
        images = self.client.get(f"{self.url}?type=image").context["clips"]

        self.assertEqual([c.pk for c in videos], [clip.pk])
        self.assertEqual([c.pk for c in images], [shot.pk])

    def test_絞り込みの件数は自分のぶんだけ数える(self):
        ClipFactory.create_batch(2, user=self.user)
        ClipFactory(user=self.user, video=True)
        ClipFactory.create_batch(5, user=self.other)

        response = self.client.get(self.url)

        self.assertEqual(response.context["total_count"], 3)
        self.assertEqual(response.context["image_count"], 2)
        self.assertEqual(response.context["video_count"], 1)

    def test_12件を超えるとページが分かれる(self):
        ClipFactory.create_batch(13, user=self.user)

        first = self.client.get(self.url)
        second = self.client.get(f"{self.url}?page=2")

        self.assertEqual(len(first.context["clips"]), 12)
        self.assertEqual(len(second.context["clips"]), 1)

    def test_保存が無いときは案内を出す(self):
        response = self.client.get(self.url)

        self.assertContains(response, "まだ何も保存していません")

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class ClipFileAccessTests(MediaTestCase):
    """保存したファイルは本人だけが取得できる。"""

    def setUp(self):
        self.user = UserFactory()
        self.other = UserFactory()
        self.clip = ClipFactory(user=self.user)

    def test_本人は閲覧できる(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("clips:file", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 200)

    def test_他人は閲覧できない(self):
        self.client.force_login(self.other)

        response = self.client.get(reverse("clips:file", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 404)

    def test_本人はダウンロードできる(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("clips:download", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])

    def test_他人はダウンロードできない(self):
        self.client.force_login(self.other)

        response = self.client.get(reverse("clips:download", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 404)

    def test_未ログインでは取得できない(self):
        response = self.client.get(reverse("clips:file", args=[self.clip.pk]))

        self.assertEqual(response.status_code, 302)

    def test_一覧用のサムネイルは動きを止めて返す(self):
        self.client.force_login(self.user)
        clip = ClipFactory(user=self.user, video=True)

        response = self.client.get(reverse("clips:thumbnail", args=[clip.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"@keyframes", response.content)
