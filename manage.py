#!/usr/bin/env python
"""Django のコマンドラインユーティリティ。"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django をインポートできませんでした。インストール済みか、"
            "仮想環境が有効になっているかを確認してください。"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
