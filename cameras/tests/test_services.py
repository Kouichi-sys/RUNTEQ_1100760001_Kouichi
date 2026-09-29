"""過去映像の再生位置を決める処理の単体テスト。"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from cameras import services


class ResolvePlaybackStartTests(TestCase):
    def setUp(self):
        self.now = timezone.localtime()

    def test_指定が無ければ1時間前(self):
        start, error = services.resolve_playback_start(None, None, self.now)

        self.assertIsNone(error)
        self.assertEqual(start, self.now - timedelta(minutes=60))

    def test_日付と時刻を指定できる(self):
        at = self.now - timedelta(days=1, hours=3)

        start, error = services.resolve_playback_start(
            at.strftime("%Y-%m-%d"), at.strftime("%H:%M"), self.now
        )

        self.assertIsNone(error)
        self.assertEqual(start.strftime("%Y-%m-%d %H:%M"), at.strftime("%Y-%m-%d %H:%M"))

    def test_日付だけなら時刻を既定値で補う(self):
        at = self.now - timedelta(days=1)
        default = self.now - timedelta(minutes=60)

        start, error = services.resolve_playback_start(
            at.strftime("%Y-%m-%d"), None, self.now
        )

        self.assertIsNone(error)
        self.assertEqual(start.strftime("%H:%M"), default.strftime("%H:%M"))

    def test_未来は現在に戻して理由を返す(self):
        future = self.now + timedelta(days=1)

        start, error = services.resolve_playback_start(
            future.strftime("%Y-%m-%d"), "12:00", self.now
        )

        self.assertEqual(start, self.now)
        self.assertIn("未来の日時は指定できません", error)

    def test_読み取れない値は既定値に戻して理由を返す(self):
        start, error = services.resolve_playback_start("2026-13-45", "99:99", self.now)

        self.assertEqual(start, self.now - timedelta(minutes=60))
        self.assertIn("読み取れませんでした", error)

    def test_空白だけの指定は未指定として扱う(self):
        start, error = services.resolve_playback_start("  ", "  ", self.now)

        self.assertIsNone(error)
        self.assertEqual(start, self.now - timedelta(minutes=60))


class PlaybackShortcutsTests(TestCase):
    def test_よく使う範囲を日付と時刻で返す(self):
        now = timezone.localtime()

        shortcuts = services.playback_shortcuts(now)

        self.assertEqual(len(shortcuts), 4)
        self.assertEqual(shortcuts[0]["label"], "10分前")
        self.assertEqual(
            shortcuts[0]["time"], (now - timedelta(minutes=10)).strftime("%H:%M")
        )
        self.assertEqual(shortcuts[-1]["label"], "昨日の今ごろ")
