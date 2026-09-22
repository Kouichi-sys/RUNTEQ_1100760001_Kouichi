from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class LoginForm(AuthenticationForm):
    """標準のログインフォームに、入力欄の見た目と補助表示を足したもの。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "placeholder": "you@example.com",
            "autocomplete": "email",
            "autofocus": True,
        })
        self.fields["password"].widget.attrs.update({
            "placeholder": "パスワード",
            "autocomplete": "current-password",
        })


class SignupForm(UserCreationForm):
    """社内アカウントの新規登録フォーム。

    ログインはemailで行うため、usernameではなくemailとnameを入力させる。
    """

    class Meta:
        model = User
        fields = ("email", "name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({
            "placeholder": "you@example.com",
            "autocomplete": "email",
            "autofocus": True,
        })
        self.fields["name"].widget.attrs.update({
            "placeholder": "現場 太郎",
            "autocomplete": "name",
        })
        self.fields["password1"].widget.attrs.update({
            "placeholder": "パスワード",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "placeholder": "パスワード(確認用)",
            "autocomplete": "new-password",
        })
