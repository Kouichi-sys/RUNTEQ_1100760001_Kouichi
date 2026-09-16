FROM python:3.12-slim

# Pythonの出力をバッファリングせず即座にログへ流す/.pycを作らない
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依存だけ先に入れることで、アプリのコード変更時にキャッシュを効かせる
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
