"""ファイルを保存するテストのための土台。"""

import shutil
import tempfile

from django.test import TestCase, override_settings


class MediaTestCase(TestCase):
    """MEDIA_ROOTを一時領域に向けるTestCase。

    クリップのテストは実ファイルを作るため、そのまま動かすと開発用の
    media/ にゴミが溜まる。テストのあいだだけ保存先を移し、終わったら消す。
    """

    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp(prefix="nxv-test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
