from django.db import IntegrityError
from django.test import TestCase

from accounts.factories import UserFactory
from accounts.models import User


class UserModelTests(TestCase):
    """社内アカウント。ログインはemailのみで行う。"""

    def test_emailとパスワードでユーザーを作れる(self):
        user = User.objects.create_user(
            email="genba@example.com", password="test-password-1234", name="現場 太郎"
        )

        self.assertEqual(user.email, "genba@example.com")
        self.assertEqual(user.name, "現場 太郎")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_emailは必須(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="test-password-1234", name="名無し")

    def test_emailは重複できない(self):
        UserFactory(email="duplicate@example.com")

        with self.assertRaises(IntegrityError):
            UserFactory(email="duplicate@example.com")

    def test_emailは大文字小文字を揃えて保存される(self):
        # ドメイン部分はnormalize_emailで小文字になる
        user = User.objects.create_user(
            email="Genba@EXAMPLE.COM", password="test-password-1234", name="現場 太郎"
        )

        self.assertEqual(user.email, "Genba@example.com")

    def test_パスワードはハッシュ化して保存される(self):
        user = User.objects.create_user(
            email="genba@example.com", password="test-password-1234", name="現場 太郎"
        )

        self.assertNotEqual(user.password, "test-password-1234")
        self.assertTrue(user.check_password("test-password-1234"))

    def test_ログインの識別子はemail(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertNotIn("username", [field.name for field in User._meta.get_fields()])

    def test_文字列表現はemail(self):
        user = UserFactory(email="genba@example.com")

        self.assertEqual(str(user), "genba@example.com")

    def test_テーブル名はusers(self):
        self.assertEqual(User._meta.db_table, "users")


class SuperUserTests(TestCase):
    def test_管理者を作れる(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="test-password-1234", name="管理者"
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_is_staffがFalseだと管理者にできない(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com",
                password="test-password-1234",
                name="管理者",
                is_staff=False,
            )

    def test_is_superuserがFalseだと管理者にできない(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com",
                password="test-password-1234",
                name="管理者",
                is_superuser=False,
            )
