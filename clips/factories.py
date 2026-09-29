"""テスト用のクリップ・スクリーンショットを作るfactory。

実ファイルを伴うため、使うテストでは MEDIA_ROOT を一時領域に向けること
(clips.tests.base.MediaTestCase を使うと自動で切り替わる)。
"""

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory, FileField

from accounts.factories import UserFactory
from cameras.factories import CameraFactory

from .models import Clip

# 中身は問わないが、保存形式に合わせてSVGにしておく
DUMMY_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360"></svg>'


class ClipFactory(DjangoModelFactory):
    """既定はスクリーンショット。動画にするときは video=True を渡す。"""

    class Meta:
        model = Clip

    class Params:
        # ClipFactory(video=True) でクリップ(動画)になる
        video = factory.Trait(
            media_type=Clip.VIDEO,
            seconds=60,
            title=factory.Sequence(lambda n: f"クリップ{n}"),
        )

    user = factory.SubFactory(UserFactory)
    camera = factory.SubFactory(CameraFactory)
    title = factory.Sequence(lambda n: f"スクリーンショット{n}")
    file = FileField(filename="clip.svg", data=DUMMY_SVG)
    media_type = Clip.IMAGE
    seconds = 0
    taken_at = factory.LazyFunction(timezone.now)
    memo = ""
