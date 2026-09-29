import os

from django.conf import settings

from clips.factories import ClipFactory
from clips.models import Clip
from clips.tests.base import MediaTestCase


class ClipFactoryTests(MediaTestCase):
    def test_既定ではスクリーンショットになる(self):
        clip = ClipFactory()

        self.assertEqual(clip.media_type, Clip.IMAGE)
        self.assertEqual(clip.seconds, 0)
        self.assertFalse(clip.is_video)

    def test_videoを指定するとクリップになる(self):
        clip = ClipFactory(video=True)

        self.assertEqual(clip.media_type, Clip.VIDEO)
        self.assertEqual(clip.seconds, 60)
        self.assertTrue(clip.is_video)

    def test_実ファイルが作られる(self):
        clip = ClipFactory()

        path = os.path.join(settings.MEDIA_ROOT, clip.file.name)
        self.assertTrue(os.path.exists(path))

    def test_テスト用の保存先に作られる(self):
        clip = ClipFactory()

        # 開発用のmedia/を汚さないこと
        self.assertTrue(str(settings.MEDIA_ROOT).startswith("/tmp/"))
        self.assertTrue(clip.file.name.startswith("clips/"))

    def test_保存者とカメラも一緒に作られる(self):
        clip = ClipFactory()

        self.assertTrue(clip.user.pk)
        self.assertTrue(clip.camera.server.pk)

    def test_保存者を指定して複数作れる(self):
        clip = ClipFactory()
        others = ClipFactory.create_batch(2, user=clip.user)

        self.assertEqual(Clip.objects.filter(user=clip.user).count(), 3)
        self.assertEqual({c.user_id for c in others}, {clip.user.pk})
