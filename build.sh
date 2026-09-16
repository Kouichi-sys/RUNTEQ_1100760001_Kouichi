#!/usr/bin/env bash
# Renderのビルド時に実行されるスクリプト
set -o errexit

pip install -r requirements.txt

# 静的ファイルを集約する(whitenoiseが配信するため必須)
python manage.py collectstatic --no-input

python manage.py migrate

# レビュー用のデモアカウントを用意する(環境変数が未設定なら何もしない)
python manage.py create_demo_user
