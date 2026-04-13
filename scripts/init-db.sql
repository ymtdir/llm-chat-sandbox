-- テスト用データベースの作成
CREATE DATABASE ai_diary_companion_test;

-- 必要に応じて拡張機能を有効化
\c ai_diary_companion;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c ai_diary_companion_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";