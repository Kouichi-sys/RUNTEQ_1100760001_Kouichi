from django.test import TestCase

from accounts.factories import DEFAULT_PASSWORD, UserFactory
from accounts.models import User


class UserFactoryTests(TestCase):
    def test_ユーザーを作成できる(self):
        user = UserFactory()

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_emailが重複しない(self):
        first = UserFactory()
        second = UserFactory()

        self.assertNotEqual(first.email, second.email)

    def test_パスワードはハッシュ化して保存される(self):
        user = UserFactory()

        self.assertNotEqual(user.password, DEFAULT_PASSWORD)
        self.assertTrue(user.check_password(DEFAULT_PASSWORD))

    def test_パスワードを指定できる(self):
        user = UserFactory(password="another-password-5678")

        self.assertTrue(user.check_password("another-password-5678"))
