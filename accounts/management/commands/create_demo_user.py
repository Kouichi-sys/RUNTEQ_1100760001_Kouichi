import os

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    """レビュー用の公開環境にデモアカウントを用意する。

    本アプリには利用者自身によるアカウント登録機能が無いため、
    デプロイ時にこのコマンドでログイン用のアカウントを作成する。
    環境変数が設定されていないときは何もしない(社内本番環境では作られない)。
    """

    help = "環境変数からデモ用アカウントを作成・更新する"

    def handle(self, *args, **options):
        email = os.environ.get("DEMO_USER_EMAIL")
        password = os.environ.get("DEMO_USER_PASSWORD")
        name = os.environ.get("DEMO_USER_NAME", "デモユーザー")

        if not email or not password:
            self.stdout.write(
                "DEMO_USER_EMAIL / DEMO_USER_PASSWORD が未設定のため、"
                "デモアカウントは作成しません。"
            )
            return

        user, created = User.objects.get_or_create(
            email=email, defaults={"name": name}
        )
        user.name = name
        # 再デプロイのたびにパスワードを設定し直し、確実にログインできる状態を保つ
        user.set_password(password)
        user.is_active = True
        user.save()

        action = "作成" if created else "更新"
        self.stdout.write(self.style.SUCCESS(f"デモアカウントを{action}しました: {email}"))
