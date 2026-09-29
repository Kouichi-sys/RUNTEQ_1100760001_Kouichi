from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from cameras.factories import ServerFactory
from cameras.models import Camera, Server


class CreateDemoCamerasTests(TestCase):
    """レビュー環境にサンプル構成を用意するコマンド。"""

    def run_command(self, **options):
        out = StringIO()
        call_command("create_demo_cameras", stdout=out, **options)
        return out.getvalue()

    @override_settings(VIDEO_SOURCE="mock")
    def test_mockのときはサンプル構成を作る(self):
        self.run_command()

        self.assertEqual(Server.objects.count(), 4)
        self.assertEqual(Camera.objects.count(), 12)
        self.assertTrue(Server.objects.filter(name="缶2号列").exists())

    @override_settings(VIDEO_SOURCE="mock")
    def test_何度実行しても増えない(self):
        self.run_command()
        self.run_command()

        self.assertEqual(Server.objects.count(), 4)
        self.assertEqual(Camera.objects.count(), 12)

    @override_settings(VIDEO_SOURCE="mock")
    def test_定義から外れたサーバーは消える(self):
        ServerFactory(name="古い列")

        self.run_command()

        self.assertFalse(Server.objects.filter(name="古い列").exists())

    @override_settings(VIDEO_SOURCE="nx")
    def test_実機のときは作らない(self):
        output = self.run_command()

        self.assertEqual(Server.objects.count(), 0)
        self.assertIn("作成しません", output)

    @override_settings(VIDEO_SOURCE="nx")
    def test_forceを付ければ実機設定でも作れる(self):
        self.run_command(force=True)

        self.assertEqual(Server.objects.count(), 4)
