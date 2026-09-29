"""テスト用のサーバー・カメラを作るfactory。"""

import factory
from factory.django import DjangoModelFactory

from .models import Camera, Server


class ServerFactory(DjangoModelFactory):
    """カメラ列(NxWitnessサーバー)。"""

    class Meta:
        model = Server

    name = factory.Sequence(lambda n: f"缶{n}号列")
    address = factory.Sequence(lambda n: f"https://192.168.10.{n % 250 + 1}:7001")
    line = "缶ライン"


class CameraFactory(DjangoModelFactory):
    """サーバーにぶら下がるカメラ。"""

    class Meta:
        model = Camera

    server = factory.SubFactory(ServerFactory)
    name = factory.Sequence(lambda n: f"充填機{n}")
