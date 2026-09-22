from django import forms

from .models import Clip


class ClipForm(forms.ModelForm):
    """クリップ保存フォーム。映像・カメラ・日時はサーバー側で決めるため入力させない。"""

    class Meta:
        model = Clip
        fields = ("title", "memo")
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "例: 缶詰まり発生時の様子",
                "autofocus": True,
            }),
            "memo": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "状況や対応内容を書いておくと、後で報告書に使えます。",
            }),
        }
