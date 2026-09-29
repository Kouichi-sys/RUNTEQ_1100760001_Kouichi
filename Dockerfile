FROM python:3.12-slim

# Pythonの出力をバッファリングせず即座にログへ流す/.pycを作らない
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依存だけ先に入れることで、アプリのコード変更時にキャッシュを効かせる
COPY requirements.txt requirements-dev.txt /app/
# 開発用コンテナではテスト用の依存も入れる。本番(Render)は requirements.txt だけを使う
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
