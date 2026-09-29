"""テスト用のユーザーを作るfactory。"""

import factory
from factory.django import DjangoModelFactory

from .models import User

# テストで使う既定のパスワード。テスト側からログインするときにも使う
DEFAULT_PASSWORD = "test-password-1234"


class UserFactory(DjangoModelFactory):
    """社内アカウント。emailは重複しないよう連番で作る。"""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Sequence(lambda n: f"現場 太郎{n}")
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """生のパスワードを持たせず、必ずハッシュ化して保存する。"""
        if not create:
            return
        self.set_password(extracted or DEFAULT_PASSWORD)
        self.save()
