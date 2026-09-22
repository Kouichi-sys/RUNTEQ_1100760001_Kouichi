from django.core.management.base import BaseCommand

from cameras.models import Camera, Server

# レビュー用のサンプル構成(製造ライン3本ぶんのカメラ列)
DEMO_SERVERS = [
    {
        "name": "A列サーバー",
        "address": "https://192.168.10.11:7001",
        "line": "第1製造ライン",
        "cameras": ["1号機 正面", "1号機 側面", "搬送コンベア 入口"],
    },
    {
        "name": "B列サーバー",
        "address": "https://192.168.10.12:7001",
        "line": "第2製造ライン",
        "cameras": ["2号機 正面", "2号機 充填部", "検査装置 出口"],
    },
    {
        "name": "C列サーバー",
        "address": "https://192.168.10.13:7001",
        "line": "梱包ライン",
        "cameras": ["梱包機 全体", "パレタイザ"],
    },
]


class Command(BaseCommand):
    """レビュー用にサーバー・カメラのサンプルデータを用意する。

    NxWitness本体は社内LAN内にしか無く公開環境からは到達できないため、
    画面の動作確認ができるようダミーの構成を投入する。
    何度実行しても同じ状態になる(重複して増えない)。
    """

    help = "デモ用のサーバー・カメラを作成する"

    def handle(self, *args, **options):
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

            action = "作成" if created else "更新"
            self.stdout.write(f"{server.name} を{action}しました(カメラ {len(entry['cameras'])} 台)")

        self.stdout.write(self.style.SUCCESS("デモ用のサーバー・カメラを用意しました。"))
