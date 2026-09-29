from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.factories import UserFactory
from cameras.factories import CameraFactory, ServerFactory


class DashboardTests(TestCase):
    """ログイン後のダッシュボード。カメラ列を選ぶ入り口。"""

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("pages:home")
        self.client.force_login(self.user)

    def test_カメラ列の一覧が出る(self):
        server = ServerFactory(name="缶2号列", line="缶ライン")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "缶2号列")
        self.assertContains(response, "缶ライン")

    def test_カメラの台数が出る(self):
        server = ServerFactory()
        CameraFactory.create_batch(3, server=server)

        response = self.client.get(self.url)

        self.assertContains(response, "カメラ 3 台")

    def test_登録が無いときは案内を出す(self):
        response = self.client.get(self.url)

        self.assertContains(response, "登録されていません")

    def test_一覧はまとめて数える(self):
        for _ in range(3):
            CameraFactory.create_batch(2, server=ServerFactory())

        # サーバーごとにカメラを数え直さないこと(N+1にしない)
        with self.assertNumQueries(3):
            self.client.get(self.url)

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class ServerDetailTests(TestCase):
    """カメラ列に属するカメラの一覧。"""

    def setUp(self):
        self.user = UserFactory()
        self.server = ServerFactory(name="瓶列")
        self.client.force_login(self.user)
        self.url = reverse("cameras:server_detail", args=[self.server.pk])

    def test_カメラの一覧が出る(self):
        CameraFactory(server=self.server, name="洗瓶機")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "洗瓶機")

    def test_カメラが無いときは案内を出す(self):
        response = self.client.get(self.url)

        self.assertContains(response, "カメラが登録されていません")

    def test_カメラをまとめて取る(self):
        CameraFactory.create_batch(5, server=self.server)

        with self.assertNumQueries(4):
            self.client.get(self.url)

    def test_存在しないサーバーは404(self):
        response = self.client.get(reverse("cameras:server_detail", args=[9999]))

        self.assertEqual(response.status_code, 404)

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class CameraLiveTests(TestCase):
    """カメラ1台のライブ映像。"""

    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.client.force_login(self.user)
        self.url = reverse("cameras:camera_live", args=[self.camera.pk])

    def test_映像が埋め込まれる(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<svg")
        self.assertContains(response, "@keyframes nxv-flow")

    def test_LIVE表示になる(self):
        response = self.client.get(self.url)

        self.assertContains(response, "● LIVE")

    def test_過去映像への導線がある(self):
        response = self.client.get(self.url)

        self.assertContains(response, reverse("cameras:playback", args=[self.camera.pk]))

    def test_存在しないカメラは404(self):
        response = self.client.get(reverse("cameras:camera_live", args=[9999]))

        self.assertEqual(response.status_code, 404)

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class PlaybackTests(TestCase):
    """過去映像。日時を指定してその時点から再生する。"""

    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.client.force_login(self.user)
        self.url = reverse("cameras:playback", args=[self.camera.pk])

    def test_既定では1時間前から再生する(self):
        expected = timezone.localtime() - timedelta(minutes=60)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected.strftime("%Y-%m-%d"))
        self.assertContains(response, expected.strftime("%H:%M"))

    def test_日付と時刻を指定できる(self):
        at = timezone.localtime() - timedelta(days=1, hours=3)

        response = self.client.get(
            self.url, {"date": at.strftime("%Y-%m-%d"), "time": at.strftime("%H:%M")}
        )

        self.assertContains(response, at.strftime("%Y-%m-%dT%H:%M"))

    def test_日付だけ指定すると時刻は既定値で補う(self):
        at = timezone.localtime() - timedelta(days=1)
        default_time = (timezone.localtime() - timedelta(minutes=60)).strftime("%H:%M")

        response = self.client.get(self.url, {"date": at.strftime("%Y-%m-%d")})

        self.assertContains(response, default_time)

    def test_未来を指定すると理由を出して現在に戻す(self):
        future = timezone.localtime() + timedelta(days=1)

        response = self.client.get(
            self.url, {"date": future.strftime("%Y-%m-%d"), "time": "12:00"}
        )

        self.assertContains(response, "未来の日時は指定できません")

    def test_読み取れない値は理由を出して既定値に戻す(self):
        response = self.client.get(self.url, {"date": "2026-13-45", "time": "99:99"})

        self.assertContains(response, "読み取れませんでした")

    def test_再生中と表示される(self):
        response = self.client.get(self.url)

        self.assertContains(response, "▶ 再生中")
        self.assertNotContains(response, "● LIVE")

    def test_巻き戻しと早送りの操作がある(self):
        response = self.client.get(self.url)

        for jump in ("-60", "-10", "10", "60"):
            self.assertContains(response, f'data-jump="{jump}"')

    def test_ライブへの導線がある(self):
        response = self.client.get(self.url)

        self.assertContains(response, reverse("cameras:camera_live", args=[self.camera.pk]))

    def test_未ログインではログイン画面に飛ぶ(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class StreamAndImageTests(TestCase):
    """映像の取得先。再生位置を変えたときや一覧のサムネイルで使う。"""

    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.client.force_login(self.user)

    def test_動く映像を取得できる(self):
        response = self.client.get(reverse("cameras:stream", args=[self.camera.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"@keyframes nxv-flow", response.content)

    def test_静止画を取得できる(self):
        response = self.client.get(reverse("cameras:live_image", args=[self.camera.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"@keyframes", response.content)

    def test_時刻が違えば絵も変わる(self):
        at = timezone.now() - timedelta(hours=2)
        url = reverse("cameras:live_image", args=[self.camera.pk])

        first = self.client.get(url, {"at": at.isoformat()}).content
        second = self.client.get(
            url, {"at": (at + timedelta(seconds=1)).isoformat()}
        ).content

        self.assertNotEqual(first, second)

    def test_常に最新を返すためキャッシュさせない(self):
        response = self.client.get(reverse("cameras:stream", args=[self.camera.pk]))

        self.assertIn("no-store", response["Cache-Control"])

    def test_存在しないカメラは404(self):
        response = self.client.get(reverse("cameras:stream", args=[9999]))

        self.assertEqual(response.status_code, 404)

    def test_未ログインでは取得できない(self):
        self.client.logout()

        response = self.client.get(reverse("cameras:stream", args=[self.camera.pk]))

        self.assertEqual(response.status_code, 302)
