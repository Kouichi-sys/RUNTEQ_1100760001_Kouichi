from django.conf import settings
from django.core.management.base import BaseCommand

from cameras.models import Camera, Server

# レビュー用のサンプル構成(ビール工場の製造ライン4列)
DEMO_SERVERS = [
    {
        "name": "缶2号列",
        "address": "https://192.168.10.11:7001",
        "line": "缶ライン",
        "cameras": ["充填機", "シーマー(巻締機)", "パレタイザ"],
    },
    {
        "name": "缶3号列",
        "address": "https://192.168.10.12:7001",
        "line": "缶ライン",
        "cameras": ["充填機", "シーマー(巻締機)", "ケーサー"],
    },
    {
        "name": "瓶列",
        "address": "https://192.168.10.13:7001",
        "line": "瓶ライン",
        "cameras": ["洗瓶機", "充填機", "ラベラー"],
    },
    {
        "name": "樽列",
        "address": "https://192.168.10.14:7001",
        "line": "樽ライン",
        "cameras": ["樽洗浄機", "充填機", "パレタイザ"],
    },
]


class Command(BaseCommand):
    """レビュー用にサーバー・カメラのサンプルデータを用意する。

    NxWitness本体は社内LAN内にしか無く公開環境からは到達できないため、
    画面の動作確認ができるようダミーの構成を投入する。
    何度実行しても同じ状態になる(重複して増えない)。

    投入するのは VIDEO_SOURCE=mock のときだけ。社内本番は VIDEO_SOURCE=nx で
    実物のNxWitnessを見るため、ダミーデータは入らない。
    """

    help = "デモ用のサーバー・カメラを作成する(VIDEO_SOURCE=mock のときのみ)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="VIDEO_SOURCEの値にかかわらず投入する",
        )

    def handle(self, *args, **options):
        if settings.VIDEO_SOURCE != "mock" and not options["force"]:
            self.stdout.write(
                f"VIDEO_SOURCE={settings.VIDEO_SOURCE} のため、"
                "デモ用のサーバー・カメラは作成しません。"
            )
            return

        for entry in DEMO_SERVERS:
            server, created = Server.objects.get_or_create(
                name=entry["name"],
                defaults={"address": entry["address"], "line": entry["line"]},
            )
            server.address = entry["address"]
            server.line = entry["line"]
            server.save()

            for camera_name in entry["cameras"]:
                Camera.objects.get_or_create(server=server, name=camera_name)

            # 構成を変えたときに古いカメラが残らないようにする
            removed = server.cameras.exclude(name__in=entry["cameras"]).delete()[0]

            action = "作成" if created else "更新"
            note = f" / 古いカメラ {removed} 台を削除" if removed else ""
            self.stdout.write(
                f"{server.name} を{action}しました(カメラ {len(entry['cameras'])} 台){note}"
            )

        # 定義から外したサーバーを残さない(カメラも一緒に消える)
        stale = Server.objects.exclude(name__in=[e["name"] for e in DEMO_SERVERS])
        for name in stale.values_list("name", flat=True):
            self.stdout.write(f"{name} は定義から外れたため削除します")
        stale.delete()

        self.stdout.write(self.style.SUCCESS("デモ用のサーバー・カメラを用意しました。"))
