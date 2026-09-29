from django.test import TestCase
from django.urls import reverse

from accounts.factories import DEFAULT_PASSWORD, UserFactory
from accounts.models import User


class LoginTests(TestCase):
    """トップページがログイン画面を兼ねる。"""

    def setUp(self):
        self.user = UserFactory(email="genba@example.com")
        self.url = reverse("accounts:login")

    def test_ログイン画面が開く(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ログイン")

    def test_emailとパスワードでログインできる(self):
        response = self.client.post(
            self.url, {"username": "genba@example.com", "password": DEFAULT_PASSWORD}
        )

        self.assertRedirects(response, reverse("pages:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_パスワードが違うとログインできない(self):
        response = self.client.post(
            self.url, {"username": "genba@example.com", "password": "wrong-password"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_存在しないemailではログインできない(self):
        response = self.client.post(
            self.url, {"username": "nobody@example.com", "password": DEFAULT_PASSWORD}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_無効なユーザーはログインできない(self):
        self.user.is_active = False
        self.user.save()

        self.client.post(
            self.url, {"username": "genba@example.com", "password": DEFAULT_PASSWORD}
        )

        self.assertNotIn("_auth_user_id", self.client.session)

    def test_ログイン済みならダッシュボードへ送る(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("pages:home"))

    def test_新規登録への導線がある(self):
        response = self.client.get(self.url)

        self.assertContains(response, reverse("accounts:signup"))


class LogoutTests(TestCase):
    def test_ログアウトするとログイン画面に戻る(self):
        self.client.force_login(UserFactory())

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class SignupTests(TestCase):
    """社内アカウントの新規登録。登録後はそのままログイン状態にする。"""

    def setUp(self):
        self.url = reverse("accounts:signup")
        self.valid = {
            "email": "newbie@example.com",
            "name": "現場 花子",
            "password1": "Genba-Camera-2026",
            "password2": "Genba-Camera-2026",
        }

    def test_登録画面が開く(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "新規登録")

    def test_登録できる(self):
        response = self.client.post(self.url, self.valid)

        self.assertRedirects(response, reverse("pages:home"))
        user = User.objects.get(email="newbie@example.com")
        self.assertEqual(user.name, "現場 花子")

    def test_登録するとそのままログイン状態になる(self):
        self.client.post(self.url, self.valid)

        self.assertEqual(self.client.get(reverse("pages:home")).status_code, 200)

    def test_パスワードはハッシュ化して保存される(self):
        self.client.post(self.url, self.valid)

        user = User.objects.get(email="newbie@example.com")
        self.assertNotEqual(user.password, "Genba-Camera-2026")
        self.assertTrue(user.check_password("Genba-Camera-2026"))

    def test_emailが重複すると登録できない(self):
        UserFactory(email="newbie@example.com")

        response = self.client.post(self.url, self.valid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="newbie@example.com").count(), 1)

    def test_パスワードが一致しないと登録できない(self):
        response = self.client.post(
            self.url, {**self.valid, "password2": "Different-Password-9999"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="newbie@example.com").exists())

    def test_単純すぎるパスワードは登録できない(self):
        response = self.client.post(
            self.url, {**self.valid, "password1": "password", "password2": "password"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="newbie@example.com").exists())

    def test_ログイン済みならダッシュボードへ送る(self):
        self.client.force_login(UserFactory())

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("pages:home"))
