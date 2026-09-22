#!/usr/bin/env bash
# Renderのビルド時に実行されるスクリプト
set -o errexit

pip install -r requirements.txt

# 静的ファイルを集約する(whitenoiseが配信するため必須)
python manage.py collectstatic --no-input

python manage.py migrate

# レビュー用のデモアカウントを用意する(環境変数が未設定なら何もしない)
python manage.py create_demo_user

# レビュー用のサンプル構成(サーバー・カメラ)を用意する。
# 社内本番環境にダミーデータが入らないよう、環境変数で明示的に有効化したときだけ実行する。
if [ "${CREATE_DEMO_CAMERAS}" = "true" ]; then
  python manage.py create_demo_cameras
fi
