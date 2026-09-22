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
# VIDEO_SOURCE=mock のときだけ投入されるため、社内本番(nx)にダミーは入らない。
python manage.py create_demo_cameras
