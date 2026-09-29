"""件数が増えても問い合わせ回数が変わらないことを確かめる。

N+1は、データが少ないうちは気付けない。ここでは「1件のとき」と
「たくさんあるとき」で回数が同じであることを確かめ、あとから
select_related などを外してしまった場合に気付けるようにする。
"""

from django.test import TestCase
from django.urls import reverse

from accounts.factories import UserFactory
from cameras.factories import CameraFactory, ServerFactory
from clips.factories import ClipFactory
from clips.tests.base import MediaTestCase


class DashboardQueryTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("pages:home")

    def test_カメラ列が増えても回数が変わらない(self):
        ServerFactory()
        with self.assertNumQueries(3):
            self.client.get(self.url)

        for _ in range(10):
            CameraFactory.create_batch(3, server=ServerFactory())

        with self.assertNumQueries(3):
            self.client.get(self.url)


class ServerDetailQueryTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.server = ServerFactory()
        self.client.force_login(self.user)
        self.url = reverse("cameras:server_detail", args=[self.server.pk])

    def test_カメラが増えても回数が変わらない(self):
        CameraFactory(server=self.server)
        with self.assertNumQueries(4):
            self.client.get(self.url)

        CameraFactory.create_batch(20, server=self.server)

        with self.assertNumQueries(4):
            self.client.get(self.url)


class MyPageQueryTests(MediaTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("clips:mypage")

    def test_保存が増えても回数が変わらない(self):
        # カメラもサーバーも別々にすると、たどるたびに問い合わせが増えやすい
        ClipFactory(user=self.user)
        with self.assertNumQueries(5):
            self.client.get(self.url)

        for _ in range(11):
            ClipFactory(user=self.user, camera=CameraFactory())

        with self.assertNumQueries(5):
            self.client.get(self.url)

    def test_絞り込んでも回数が変わらない(self):
        ClipFactory.create_batch(5, user=self.user)
        ClipFactory.create_batch(5, user=self.user, video=True)

        with self.assertNumQueries(5):
            self.client.get(f"{self.url}?type=video")

    def test_種別の件数は一度で数える(self):
        ClipFactory.create_batch(3, user=self.user)

        with self.assertNumQueries(5):
            response = self.client.get(self.url)

        # 3種類の件数が1回の問い合わせで揃うこと
        self.assertEqual(response.context["total_count"], 3)
        self.assertEqual(response.context["image_count"], 3)
        self.assertEqual(response.context["video_count"], 0)


class ClipDetailQueryTests(MediaTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.clip = ClipFactory(user=self.user)
        self.client.force_login(self.user)

    def test_詳細はカメラとサーバーをまとめて取る(self):
        with self.assertNumQueries(3):
            response = self.client.get(reverse("clips:detail", args=[self.clip.pk]))

        # テンプレートでカメラ列・ラインをたどっても増えないこと
        self.assertContains(response, self.clip.camera.server.line)

    def test_編集画面も同じ回数(self):
        with self.assertNumQueries(3):
            self.client.get(reverse("clips:edit", args=[self.clip.pk]))

    def test_削除の確認画面も同じ回数(self):
        with self.assertNumQueries(3):
            self.client.get(reverse("clips:delete", args=[self.clip.pk]))


class CameraViewQueryTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.client.force_login(self.user)

    def test_ライブはカメラとサーバーをまとめて取る(self):
        with self.assertNumQueries(3):
            response = self.client.get(
                reverse("cameras:camera_live", args=[self.camera.pk])
            )

        self.assertContains(response, self.camera.server.name)

    def test_過去映像も同じ回数(self):
        with self.assertNumQueries(3):
            self.client.get(reverse("cameras:playback", args=[self.camera.pk]))

    def test_映像の取得もまとめて取る(self):
        with self.assertNumQueries(3):
            self.client.get(reverse("cameras:stream", args=[self.camera.pk]))
