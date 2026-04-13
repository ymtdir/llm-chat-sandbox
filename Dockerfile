# Python 3.13ベースイメージ
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システム依存パッケージをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# pipをアップグレード
RUN pip install --no-cache-dir --upgrade pip

# アプリケーションコードをコピー（editable install は app/ を必要とする）
COPY . .

# 依存関係をインストール
RUN pip install --no-cache-dir -e .

# ポート8000を公開
EXPOSE 8000

# デフォルトコマンド（開発用）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]