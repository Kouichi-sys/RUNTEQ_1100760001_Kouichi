from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from accounts.models import User


class CreateDemoUserTests(TestCase):
    """レビュー環境にデモアカウントを用意するコマンド。"""

    def run_command(self):
        out = StringIO()
        call_command("create_demo_user", stdout=out)
        return out.getvalue()

    @mock.patch.dict(
        "os.environ",
        {
            "DEMO_USER_EMAIL": "demo@example.com",
            "DEMO_USER_PASSWORD": "demo-password-1234",
            "DEMO_USER_NAME": "デモユーザー",
        },
    )
    def test_環境変数があれば作る(self):
        self.run_command()

        user = User.objects.get(email="demo@example.com")
        self.assertEqual(user.name, "デモユーザー")
        self.assertTrue(user.check_password("demo-password-1234"))
        self.assertTrue(user.is_active)

    @mock.patch.dict(
        "os.environ",
        {
            "DEMO_USER_EMAIL": "demo@example.com",
            "DEMO_USER_PASSWORD": "renewed-password-5678",
        },
    )
    def test_再実行するとパスワードを入れ直す(self):
        User.objects.create_user(
            email="demo@example.com", password="old-password", name="デモユーザー"
        )

        self.run_command()

        user = User.objects.get(email="demo@example.com")
        self.assertTrue(user.check_password("renewed-password-5678"))
        self.assertEqual(User.objects.filter(email="demo@example.com").count(), 1)

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_環境変数が無ければ何もしない(self):
        output = self.run_command()

        self.assertFalse(User.objects.exists())
        self.assertIn("作成しません", output)
