import io
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from cameras.factories import CameraFactory, ServerFactory
from cameras.video_sources import MockVideoSource, NxVideoSource, get_video_source


class VideoSourceSelectionTests(TestCase):
    """VIDEO_SOURCEで取得元を切り替える。"""

    @override_settings(VIDEO_SOURCE="mock")
    def test_mockのときは疑似映像を使う(self):
        self.assertIsInstance(get_video_source(), MockVideoSource)

    @override_settings(VIDEO_SOURCE="nx")
    def test_nxのときはNxWitnessを使う(self):
        self.assertIsInstance(get_video_source(), NxVideoSource)

    @override_settings(VIDEO_SOURCE="")
    def test_未設定なら疑似映像にする(self):
        self.assertIsInstance(get_video_source(), MockVideoSource)


class MockVideoSourceTests(TestCase):
    """実カメラが無い環境で使う疑似映像。"""

    def setUp(self):
        self.source = MockVideoSource()
        self.camera = CameraFactory()
        self.now = timezone.localtime()

    def test_いつでも利用できる(self):
        self.assertTrue(self.source.is_available())

    def test_ラインごとに流れる製品が変わる(self):
        can = CameraFactory(server=ServerFactory(line="缶ライン"))
        bottle = CameraFactory(server=ServerFactory(line="瓶ライン"))
        keg = CameraFactory(server=ServerFactory(line="樽ライン"))
        other = CameraFactory(server=ServerFactory(line="不明なライン"))

        self.assertEqual(self.source.product_shape(can), "can")
        self.assertEqual(self.source.product_shape(bottle), "bottle")
        self.assertEqual(self.source.product_shape(keg), "keg")
        self.assertEqual(self.source.product_shape(other), "can")

    def test_動く映像を作れる(self):
        markup = self.source.stream_markup(self.camera, self.now)

        self.assertIn("<svg", markup)
        self.assertIn("@keyframes nxv-flow", markup)

    def test_スクリーンショットを切り出せる(self):
        content, extension, media_type = self.source.capture(self.camera, self.now)

        self.assertEqual(extension, "svg")
        self.assertEqual(media_type, "image")
        self.assertNotIn(b"@keyframes", content)

    def test_区間を切り取れる(self):
        content, extension, media_type = self.source.capture_range(
            self.camera, self.now - timedelta(minutes=1), self.now
        )

        self.assertEqual(extension, "svg")
        self.assertEqual(media_type, "video")
        self.assertIn(b"@keyframes", content)

    def test_共有用の動画を書き出せる(self):
        content, extension = self.source.export_movie(self.camera, self.now)

        self.assertEqual(extension, "gif")
        image = Image.open(io.BytesIO(content))
        self.assertEqual(image.format, "GIF")
        self.assertEqual(image.size, (640, 360))
        self.assertGreater(image.n_frames, 1)
        # 繰り返し再生されること
        self.assertEqual(image.info.get("loop"), 0)

    def test_どのラインでも動画を書き出せる(self):
        # 缶・瓶・樽で描き分けているため、それぞれ書き出せることを確かめる
        for line in ("缶ライン", "瓶ライン", "樽ライン"):
            with self.subTest(line=line):
                camera = CameraFactory(server=ServerFactory(line=line))

                content, extension = self.source.export_movie(camera, self.now)

                self.assertEqual(extension, "gif")
                self.assertEqual(Image.open(io.BytesIO(content)).format, "GIF")

    def test_時刻が違えば絵も変わる(self):
        first, _, _ = self.source.capture(self.camera, self.now)
        second, _, _ = self.source.capture(self.camera, self.now + timedelta(seconds=1))

        self.assertNotEqual(first, second)

    def test_同じ時刻なら動画も静止画も同じ位置になる(self):
        # 一時停止した場面と保存されるクリップの絵が食い違わないこと
        frame, _, _ = self.source.capture(self.camera, self.now)
        stream = self.source.stream_markup(self.camera, self.now)

        def first_position(markup):
            return markup.split("translate(")[1].split(",")[0]

        self.assertEqual(first_position(frame.decode()), first_position(stream))


class NxVideoSourceTests(TestCase):
    """実機は疎通確認(#25)のあとに実装する。"""

    def setUp(self):
        self.source = NxVideoSource()
        self.camera = CameraFactory()
        self.now = timezone.localtime()

    @override_settings(NX_BASE_URL="")
    def test_接続先が未設定なら利用できない(self):
        self.assertFalse(self.source.is_available())

    @override_settings(NX_BASE_URL="https://192.168.10.11:7001")
    def test_接続先があれば利用できる扱いにする(self):
        self.assertTrue(self.source.is_available())

    def test_映像の取得は未実装(self):
        with self.assertRaises(NotImplementedError):
            self.source.stream_markup(self.camera, self.now)
        with self.assertRaises(NotImplementedError):
            self.source.capture(self.camera, self.now)
        with self.assertRaises(NotImplementedError):
            self.source.capture_range(self.camera, self.now, self.now)
        with self.assertRaises(NotImplementedError):
            self.source.export_movie(self.camera, self.now)
