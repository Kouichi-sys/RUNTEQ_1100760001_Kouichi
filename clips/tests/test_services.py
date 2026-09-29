"""保存処理の単体テスト。画面を通さずに確かめる。"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.factories import UserFactory
from cameras.factories import CameraFactory
from clips import services
from clips.models import Clip
from clips.tests.base import MediaTestCase


class ResolveCaptureTimeTests(TestCase):
    def setUp(self):
        self.now = timezone.now()

    def test_指定が無ければいまの時刻(self):
        resolved = services.resolve_capture_time(None, self.now)

        self.assertEqual(resolved, self.now)

    def test_一時停止した時刻をそのまま使う(self):
        paused = self.now - timedelta(seconds=30)

        resolved = services.resolve_capture_time(paused.isoformat(), self.now)

        self.assertEqual(resolved, paused)

    def test_かけ離れた時刻は信用しない(self):
        old = self.now - timedelta(days=3)

        resolved = services.resolve_capture_time(old.isoformat(), self.now)

        self.assertEqual(resolved, self.now)

    def test_読み取れない値はいまの時刻(self):
        resolved = services.resolve_capture_time("こわれた値", self.now)

        self.assertEqual(resolved, self.now)


class ResolveClipRangeTests(TestCase):
    def setUp(self):
        self.now = timezone.now()

    def resolve(self, start_delta, end_delta):
        return services.resolve_clip_range(
            (self.now + start_delta).isoformat(),
            (self.now + end_delta).isoformat(),
            self.now,
        )

    def test_正しい範囲は通る(self):
        start, end, error = self.resolve(timedelta(minutes=-5), timedelta(minutes=-4))

        self.assertIsNone(error)
        self.assertEqual((end - start).total_seconds(), 60)

    def test_指定が無い(self):
        _, _, error = services.resolve_clip_range(None, None, self.now)

        self.assertEqual(error, "切り取る範囲が指定されていません。")

    def test_終了が開始より前(self):
        _, _, error = self.resolve(timedelta(0), timedelta(minutes=-1))

        self.assertEqual(error, "終了は開始より後にしてください。")

    def test_未来は指定できない(self):
        _, _, error = self.resolve(timedelta(minutes=1), timedelta(minutes=2))

        self.assertEqual(error, "未来の範囲は指定できません。")

    def test_長すぎる(self):
        _, _, error = self.resolve(timedelta(minutes=-30), timedelta(0))

        self.assertEqual(error, "範囲が長すぎます。10分以内にしてください。")

    def test_短すぎる(self):
        _, _, error = self.resolve(
            timedelta(seconds=-10), timedelta(seconds=-9, milliseconds=-500)
        )

        self.assertEqual(error, "範囲が短すぎます。1秒以上にしてください。")

    def test_ちょうど1秒は通る(self):
        start, end, error = self.resolve(timedelta(seconds=-10), timedelta(seconds=-9))

        self.assertIsNone(error)
        self.assertEqual((end - start).total_seconds(), 1)


class SaveTests(MediaTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.now = timezone.now()

    def test_スクリーンショットを保存できる(self):
        clip = services.save_screenshot(
            user=self.user,
            camera=self.camera,
            taken_at=self.now,
            title="詰まり",
            memo="横倒し",
        )

        self.assertEqual(clip.media_type, Clip.IMAGE)
        self.assertEqual(clip.seconds, 0)
        self.assertEqual(clip.taken_at, self.now)
        self.assertTrue(clip.file.name.endswith(".svg"))

    def test_クリップを保存できる(self):
        start = self.now - timedelta(minutes=2)
        end = self.now - timedelta(seconds=45)

        clip = services.save_clip(
            user=self.user,
            camera=self.camera,
            start_at=start,
            end_at=end,
            title="復旧まで",
            memo="",
        )

        self.assertEqual(clip.media_type, Clip.VIDEO)
        self.assertEqual(clip.seconds, 75)
        self.assertEqual(clip.taken_at, start)


class ConversionTests(MediaTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.camera = CameraFactory()
        self.now = timezone.now()

    def test_クリップは一覧用に静止画へ直す(self):
        clip = services.save_clip(
            user=self.user,
            camera=self.camera,
            start_at=self.now - timedelta(minutes=1),
            end_at=self.now,
            title="復旧まで",
            memo="",
        )

        self.assertTrue(services.needs_still_conversion(clip))
        self.assertNotIn("@keyframes", services.still_image(clip))

    def test_スクリーンショットは直さなくてよい(self):
        clip = services.save_screenshot(
            user=self.user, camera=self.camera, taken_at=self.now, title="詰まり", memo=""
        )

        self.assertFalse(services.needs_still_conversion(clip))
        self.assertFalse(services.needs_movie_conversion(clip))

    def test_共有用の動画を書き出せる(self):
        clip = services.save_clip(
            user=self.user,
            camera=self.camera,
            start_at=self.now - timedelta(minutes=1),
            end_at=self.now,
            title="復旧まで",
            memo="",
        )

        content, filename = services.shareable_movie(clip)

        self.assertTrue(services.needs_movie_conversion(clip))
        self.assertTrue(content.startswith(b"GIF89a"))
        self.assertTrue(filename.endswith(".gif"))
