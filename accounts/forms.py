from django.contrib.auth.forms import AuthenticationForm


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
