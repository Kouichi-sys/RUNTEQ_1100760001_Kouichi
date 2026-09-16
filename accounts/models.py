from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """usernameではなくemailを識別子として使うためのマネージャ。"""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("emailは必須です")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("スーパーユーザーはis_staff=Trueである必要があります")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("スーパーユーザーはis_superuser=Trueである必要があります")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """社内アカウント。ログインはemailのみで行う(社員番号は使わない)。"""

    email = models.EmailField("メールアドレス", unique=True)
    name = models.CharField("表示名", max_length=150)
    is_active = models.BooleanField("有効", default=True)
    is_staff = models.BooleanField("管理画面へのアクセス", default=False)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    # createsuperuser時にemail/password以外で追加入力させる項目
    REQUIRED_FIELDS = ["name"]

    class Meta:
        # ER図に合わせてテーブル名をusersにする
        db_table = "users"
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"

    def __str__(self):
        return self.email
