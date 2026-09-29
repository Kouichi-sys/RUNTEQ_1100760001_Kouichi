from django.test import TestCase

from cameras.factories import CameraFactory, ServerFactory


class ServerFactoryTests(TestCase):
    def test_サーバーを作成できる(self):
        server = ServerFactory()

        self.assertTrue(server.pk)
        self.assertTrue(server.address.startswith("https://"))

    def test_名前が重複しない(self):
        self.assertNotEqual(ServerFactory().name, ServerFactory().name)


class CameraFactoryTests(TestCase):
    def test_サーバーごと作成できる(self):
        camera = CameraFactory()

        self.assertTrue(camera.server.pk)

    def test_既存のサーバーにぶら下げられる(self):
        server = ServerFactory()
        cameras = CameraFactory.create_batch(3, server=server)

        self.assertEqual(server.cameras.count(), 3)
        self.assertEqual({c.server_id for c in cameras}, {server.pk})
