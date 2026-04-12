# 開発ガイドライン

## リポジトリ構造

### プロジェクト構造

```
llm-chat-sandbox/
├── app/                     # バックエンドアプリケーション（FastAPI）
│   ├── __init__.py
│   ├── main.py              # エントリーポイント
│   ├── core/                # コア機能（設定、セキュリティ、DB）
│   ├── models/              # SQLAlchemyモデル（データレイヤー）
│   ├── schemas/             # Pydanticスキーマ（バリデーション）
│   ├── api/                 # APIレイヤー（routes, deps, websocket）
│   ├── services/            # サービスレイヤー（ビジネスロジック）
│   ├── domain/              # ドメインレイヤー（ドメインモデル）
│   ├── repositories/        # リポジトリ（データアクセス）
│   └── scheduler/           # スケジューラー（バックグラウンドジョブ）
├── alembic/                 # マイグレーション
│   ├── versions/
│   └── env.py
├── tests/                   # テストコード
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── frontend/                # フロントエンド（React）
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── api/
│   └── package.json
├── docs/                    # プロジェクトドキュメント
│   ├── requirements.md
│   ├── basic-design.md
│   ├── detailed-design.md
│   └── development-guide.md (本ドキュメント)
├── .env.example             # 環境変数テンプレート
├── pyproject.toml           # Python依存関係・設定
├── ruff.toml                # Ruff設定
├── mypy.ini                 # mypy設定
└── README.md                # プロジェクト概要
```

### ディレクトリ詳細

#### app/core/ (コア機能)

**役割**: アプリケーション全体で使用する共通機能

**配置ファイル**:

- `config.py`: pydantic-settingsによる環境変数管理
- `security.py`: JWT認証、パスワードハッシュ化
- `database.py`: AsyncSessionの設定、DB接続

**命名規則**:

- snake_case（Python標準）

---

#### app/models/ (SQLAlchemyモデル)

**役割**: データベーステーブルの定義（データレイヤー）

**配置ファイル**:

- `user.py`: Userモデル
- `character.py`: Characterモデル
- `conversation.py`: Conversationモデル
- `message.py`: Messageモデル
- `scheduled_response.py`: ScheduledResponseモデル
- `diary.py`: Diaryモデル
- `user_fcm_token.py`: UserFcmTokenモデル

**命名規則**:

- ファイル名: snake_case
- クラス名: PascalCase（例: `ScheduledResponse`）
- テーブル名: snake_case複数形（例: `scheduled_responses`）

---

#### app/schemas/ (Pydanticスキーマ)

**役割**: リクエスト/レスポンスのバリデーション、型定義

**配置ファイル**:

- `user.py`: UserCreate, UserResponse等
- `message.py`: MessageCreate, MessageResponse等
- `diary.py`: DiaryResponse等

**命名規則**:

- ファイル名: snake_case
- クラス名: PascalCase + 用途接尾辞（`UserCreate`, `UserResponse`）

---

#### app/api/ (APIレイヤー)

**役割**: HTTPリクエストの受け付け、認証、ルーティング

**配置ファイル**:

- `deps.py`: 依存性注入（DB session取得、認証ユーザー取得）
- `routes/`: エンドポイント定義
  - `auth.py`: 認証エンドポイント
  - `conversations.py`: 会話エンドポイント
  - `messages.py`: メッセージエンドポイント
  - `diaries.py`: 日記エンドポイント
  - `characters.py`: キャラクターエンドポイント
- `websocket.py`: WebSocket接続管理

**命名規則**:

- ファイル名: snake_case
- 関数名: snake_case（FastAPIのルーター関数）

---

#### app/services/ (サービスレイヤー)

**役割**: ビジネスロジックの実装、ユースケースの実現

**配置ファイル**:

- `conversation_service.py`: 会話ロジック
- `diary_service.py`: 日記生成ロジック
- `llm_service.py`: Groq API連携

**命名規則**:

- ファイル名: snake_case
- クラス名: PascalCase + `Service`接尾辞

---

#### app/domain/ (ドメインレイヤー)

**役割**: ビジネスロジックのコア、フレームワークに依存しないロジック

**配置ファイル**:

- `character.py`: キャラクタードメインモデル（Pydantic）
- `response_timing.py`: 返信タイミング計算アルゴリズム
- `diary_generator.py`: 日記生成ロジック

**命名規則**:

- ファイル名: snake_case
- クラス名: PascalCase

---

#### app/repositories/ (リポジトリ)

**役割**: データアクセス、CRUDクエリ実行

**配置ファイル**:

- `user_repository.py`
- `conversation_repository.py`
- `message_repository.py`
- `scheduled_response_repository.py`
- `diary_repository.py`

**命名規則**:

- ファイル名: snake_case
- クラス名: PascalCase + `Repository`接尾辞

---

#### app/scheduler/ (スケジューラー)

**役割**: バックグラウンドジョブ（定期実行）

**配置ファイル**:

- `jobs.py`: APSchedulerジョブ定義（返信処理、日記生成）

---

### 命名規則

#### ディレクトリ名

- **snake_case + 複数形**: `models/`, `services/`, `repositories/`
- **単数形**: `api/`, `core/`, `domain/`（抽象的な概念）

#### ファイル名

- **Python**: snake_case（例: `conversation_service.py`）
- **TypeScript**: PascalCase（コンポーネント）、kebab-case（その他）

#### 変数・関数

**Python**:

```python
# 変数: snake_case、名詞
user_name = "John"
is_completed = True

# 関数: snake_case、動詞で始める
def fetch_user_data():
    pass

def validate_email(email: str):
    pass

# Boolean: is_, has_, should_, can_で始める
is_valid = True
has_permission = False
```

**TypeScript**:

```typescript
// 変数: camelCase
const userName = 'John';

// 関数: camelCase
function fetchUserData() {}
```

#### クラス・型

**Python**:

```python
# クラス: PascalCase + 役割接尾辞
class UserAuthenticationService:
    pass

class TaskRepository:
    pass

# Pydantic Model: PascalCase
class UserCreate(BaseModel):
    pass
```

**TypeScript**:

```typescript
// インターフェース: PascalCase
interface UserProfile {}

// 型: PascalCase
type OrderStatus = 'pending' | 'confirmed';
```

#### 定数

**Python**:

```python
# UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.groq.com"
```

**TypeScript**:

```typescript
// UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
```

---

## 開発ガイドライン

### コーディング規約（Python）

#### 関数設計

**単一責務の原則**:

```python
# ✅ 良い例: 単一の責務
def calculate_total(items: list[CartItem]) -> Decimal:
    return sum(item.price * item.quantity for item in items)

def format_price(amount: Decimal) -> str:
    return f"¥{amount:,.0f}"

# ❌ 悪い例: 複数の責務
def calculate_and_format_price(items: list[CartItem]) -> str:
    total = sum(item.price * item.quantity for item in items)
    return f"¥{total:,.0f}"
```

**関数の長さとパラメータ**:

- 目標: 20行以内、推奨: 50行以内
- パラメータが3つ以上ならPydanticモデルにまとめる

```python
# ✅ 良い例: Pydanticモデルでまとめる
class CreateUserInput(BaseModel):
    name: str
    email: EmailStr
    role: Literal['admin', 'member'] = 'member'

async def create_user(input: CreateUserInput) -> User:
    pass
```

---

#### エラーハンドリング

**カスタム例外クラス**:

```python
# app/core/exceptions.py
class AppError(Exception):
    """アプリケーション基底例外"""
    pass

class ValidationError(AppError):
    """バリデーションエラー"""
    def __init__(self, message: str, field: str):
        self.field = field
        super().__init__(message)

class NotFoundError(AppError):
    """リソース未検出エラー"""
    def __init__(self, resource: str, id: int | str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} not found: {id}")
```

**エラーハンドリングパターン**:

```python
# ✅ 良い例: 適切なエラーハンドリング
async def get_user(user_id: int, session: AsyncSession) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user

# ❌ 悪い例: エラーを無視
async def get_user(user_id: int, session: AsyncSession) -> User | None:
    try:
        user = await session.get(User, user_id)
        return user
    except Exception:
        return None  # エラー情報が失われる
```

---

#### 非同期処理

```python
# ✅ 良い例: async/awaitを使用
async def fetch_user_orders(user_id: int, session: AsyncSession) -> list[Order]:
    user = await session.get(User, user_id)
    result = await session.execute(
        select(Order).where(Order.user_id == user.id)
    )
    return result.scalars().all()

# ✅ 良い例: asyncio.gatherで並列実行
async def fetch_multiple_users(ids: list[int], session: AsyncSession) -> list[User]:
    tasks = [session.get(User, id) for id in ids]
    return await asyncio.gather(*tasks)
```

---

#### 型ヒント

```python
# ✅ 良い例: すべての関数に型ヒント
from typing import Literal

async def create_message(
    content: str,
    sender_type: Literal['user', 'character'],
    conversation_id: int,
    session: AsyncSession
) -> Message:
    pass

# ✅ 良い例: Pydanticで厳密な型定義
class CharacterConfig(BaseModel):
    personality: Literal['diligent', 'normal', 'busy']
    occupation: Literal['office_worker', 'student', 'freelancer', 'homemaker']
    working_hours: dict[str, int] | None = None
```

---

### コーディング規約（TypeScript）

#### 型安全性

```typescript
// ✅ 良い例: インターフェースで型定義
interface Message {
  id: number;
  content: string;
  senderType: 'user' | 'character';
  sentAt: Date;
}

// ✅ 良い例: Union型で状態を表現
type ResponseStatus = 'pending' | 'sent' | 'cancelled';
```

---

### Git運用ルール

#### ブランチ戦略

```
main (本番環境)
└── develop (開発環境) ※プロトタイプでは不要、mainのみで運用可
    ├── feature/* (新機能開発)
    ├── fix/* (バグ修正)
    └── refactor/* (リファクタリング)
```

**運用ルール**:

- **main**: 本番リリース済みの安定版コードのみ
- **feature/\*, fix/\***: mainから分岐し、PR経由でmainへマージ
- **直接コミット禁止**: すべての変更はPRレビューを必須
- **マージ方針**: squash mergeを推奨（コミット履歴を整理）

---

#### コミットメッセージ規約

**フォーマット**:

```
<type>: <subject>

<body>
```

**type**:

- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `docs`: ドキュメント
- `test`: テスト追加・修正
- `chore`: ビルド、設定変更

**例**:

```
feat: メッセージ送信APIを実装

- POST /api/conversations/{id}/messagesエンドポイント追加
- AI応答スケジュール機能を実装
```

---

### テスト戦略

#### テストの種類と配置

| テスト種別     | 配置先               | 命名規則                        |
| -------------- | -------------------- | ------------------------------- |
| ユニットテスト | `tests/unit/`        | `test_<module_name>.py`         |
| 統合テスト     | `tests/integration/` | `test_<feature>_integration.py` |
| E2Eテスト      | `tests/e2e/`         | `test_<scenario>_e2e.py`        |

**ディレクトリ構造**:

```
tests/
├── unit/
│   ├── services/
│   │   ├── test_conversation_service.py
│   │   └── test_diary_service.py
│   └── domain/
│       └── test_response_timing.py
├── integration/
│   └── api/
│       └── test_messages_integration.py
└── e2e/
    └── test_message_flow_e2e.py
```

---

#### テストの書き方（pytest）

**Given-When-Then パターン**:

```python
import pytest
from app.services.conversation_service import ConversationService

@pytest.mark.asyncio
async def test_send_message_creates_scheduled_response():
    # Given: 準備
    service = ConversationService(
        message_repo=mock_message_repo,
        scheduled_response_repo=mock_scheduled_response_repo,
        timing_calculator=mock_timing_calculator
    )
    user_id = 1
    conversation_id = 10
    content = "こんにちは"

    # When: 実行
    result = await service.send_message(
        user_id=user_id,
        conversation_id=conversation_id,
        content=content,
        background_tasks=mock_background_tasks
    )

    # Then: 検証
    assert result.content == "こんにちは"
    assert result.sender_type == "user"
    mock_scheduled_response_repo.create.assert_called_once()
```

---

#### カバレッジ目標

- **ビジネスロジック（サービス・ドメイン層）**: 90%以上
- **全体**: 80%以上
- **100%は目指さない**（コストと効果のバランス）

---

### コードレビュー基準

#### レビュー観点

- [ ] **機能性**: 要件を満たしているか
- [ ] **バグ**: 明らかなバグがないか
- [ ] **セキュリティ**: SQLインジェクション、XSS等の脆弱性がないか
- [ ] **パフォーマンス**: N+1問題、不要なループがないか
- [ ] **可読性**: 命名が明確か、複雑すぎないか
- [ ] **テスト**: 適切なテストが追加されているか
- [ ] **ドキュメント**: 必要に応じてコメント・ドキュメントが追加されているか

---

#### レビューコメントの書き方

**優先度を明示**:

- `[必須]`: 修正必須（セキュリティ、バグ等）
- `[推奨]`: 修正推奨（パフォーマンス、可読性等）
- `[提案]`: 検討してほしい
- `[質問]`: 理解のための質問

**建設的なフィードバック**:

```
# ❌ このコードはダメです。

# ✅ [推奨] この実装だと O(n²) の時間計算量になります。
# Mapを使うと O(n) に改善できます。

# 修正例:
user_map = {user.id: user for user in users}
target_user = user_map.get(user_id)
```

---

## 用語集

### ドメイン用語

#### Character（キャラクター）

**定義**: ユーザーと会話するAIキャラクター。性格、職業、生活パターンなどの設定を持つ。

**説明**:

- 性格（マメ/普通/忙しい）によって返信速度が変わる
- 職業（会社員/学生/フリーランス/主婦）によって返信時間帯が変わる
- JSONBフォーマットで柔軟に設定を保存

**関連用語**:

- [ScheduledResponse](#scheduledresponse予約返信)
- [ResponseTimingCalculator](#responsetimingcalculator)

**データモデル**: `app/models/character.py`, `app/domain/character.py`

**使用例**:

- 「キャラクターを作成する」: 新しいAIキャラクター設定を追加
- 「キャラクター設定を変更する」: 性格や職業を更新

---

#### ScheduledResponse（予約返信）

**定義**: AIキャラクターの返信を予約管理するエンティティ。scheduled_at（予定時刻）を持ち、APSchedulerがポーリングして実行する。

**説明**:

- ユーザーメッセージ送信時に作成される
- ResponseTimingCalculatorで計算された遅延時間後に実行予定
- status: pending → sent へ遷移

**関連用語**:

- [Character](#characterキャラクター)
- [Message](#messageメッセージ)
- [ResponseTimingCalculator](#responsetimingcalculator)

**データモデル**: `app/models/scheduled_response.py`

**状態遷移**:

| ステータス  | 意味         | 遷移条件                 | 次の状態 |
| ----------- | ------------ | ------------------------ | -------- |
| `pending`   | 予約中       | 作成時                   | `sent`   |
| `sent`      | 送信完了     | scheduled_atを過ぎて実行 | -        |
| `cancelled` | キャンセル済 | 明示的なキャンセル       | -        |

---

#### Message（メッセージ）

**定義**: 会話内の個別のメッセージ。ユーザーまたはAIキャラクターが送信。

**説明**:

- sender_type: "user" | "character"
- 最大1000文字
- sent_atでソートして会話履歴を取得

**関連用語**:

- [Conversation](#conversation会話)
- [ScheduledResponse](#scheduledresponse予約返信)

**データモデル**: `app/models/message.py`, `app/schemas/message.py`

---

#### Conversation（会話）

**定義**: ユーザーとキャラクター間の会話セッション。複数のメッセージを含む。

**関連用語**:

- [Message](#messageメッセージ)
- [User](#userユーザー)
- [Character](#characterキャラクター)

**データモデル**: `app/models/conversation.py`

---

#### Diary（日記）

**定義**: 1日の会話履歴から自動生成される日記テキスト。

**説明**:

- 1ユーザー1日1件の制約（user_id, diary_dateで複合ユニーク）
- DiaryGeneratorがLLMを使って生成
- APSchedulerで毎日深夜0時に自動生成

**関連用語**:

- [DiaryGenerator](#diarygenerator)
- [Message](#messageメッセージ)

**データモデル**: `app/models/diary.py`

---

#### User（ユーザー）

**定義**: サービスを利用するユーザー。メールアドレスとパスワードで認証。

**データモデル**: `app/models/user.py`

---

#### ResponseTimingCalculator

**定義**: キャラクターの性格・職業・時間帯を考慮して返信タイミング（遅延時間）を計算するドメインサービス。

**計算ロジック**:

1. 基本遅延時間を性格から取得（min-maxの範囲）
2. 時間帯による補正（勤務時間中は遅延が長くなる）
3. ランダム性を追加（自然な揺らぎ）
4. 既読スルーの判定

**関連用語**:

- [Character](#characterキャラクター)
- [ScheduledResponse](#scheduledresponse予約返信)

**実装**: `app/domain/response_timing.py`

---

#### DiaryGenerator

**定義**: 会話履歴から日記テキストを生成するドメインサービス。Groq APIを使用。

**処理フロー**:

1. 会話履歴を時系列で整形
2. プロンプトを構築
3. Groq APIで要約生成
4. 生成されたテキストを返却

**関連用語**:

- [Diary](#diary日記)
- [LLMService](#llmservice)

**実装**: `app/domain/diary_generator.py`

---

### 技術用語

#### FastAPI

**定義**: Python製の高速なWebフレームワーク。async/awaitネイティブサポート。

**本プロジェクトでの用途**: バックエンドAPIの構築

**バージョン**: 0.115+

**選定理由**:

- 非同期処理のネイティブサポート
- Pydantic v2統合で強力なバリデーション
- 自動OpenAPIドキュメント生成

**関連ドキュメント**:

- [基本設計書](./basic-design.md#技術スタック)

---

#### Groq

**定義**: Llama 3.3 70BなどのLLMを超高速推論できるクラウドサービス。

**本プロジェクトでの用途**: AI会話生成、日記要約生成

**選定理由**:

- OpenAI比で約1/6のコスト
- Pythonライブラリが最も成熟

**APIエンドポイント**: `https://api.groq.com/v1/chat/completions`

**モデル**: llama-3.3-70b-versatile

---

#### SQLAlchemy

**定義**: Python最大のORM（Object-Relational Mapping）ライブラリ。

**本プロジェクトでの用途**: データベースアクセス、モデル定義

**バージョン**: 2.0（async対応）

**選定理由**:

- async/awaitサポート
- 型安全なクエリビルダー
- PostgreSQLとの親和性が高い

---

#### APScheduler

**定義**: Pythonのジョブスケジューリングライブラリ。

**本プロジェクトでの用途**:

- 予約返信の定期チェック（1分ごと）
- 日記の自動生成（毎日深夜0時）

**バージョン**: 3.10+

---

#### Pydantic

**定義**: Pythonの型ヒントベースのデータバリデーションライブラリ。

**本プロジェクトでの用途**:

- リクエスト/レスポンスのバリデーション
- 環境変数管理（pydantic-settings）
- ドメインモデル定義

**バージョン**: 2.x

---

### 略語・頭字語

#### ORM

**正式名称**: Object-Relational Mapping

**意味**: オブジェクトとリレーショナルデータベースのテーブルをマッピングする技術

**本プロジェクトでの使用**: SQLAlchemyをORMとして使用

---

#### JWT

**正式名称**: JSON Web Token

**意味**: JSON形式のトークンベース認証方式

**本プロジェクトでの使用**: ユーザー認証にJWTを使用（python-jose）

---

#### LLM

**正式名称**: Large Language Model

**意味**: 大規模言語モデル

**本プロジェクトでの使用**: Groq API経由でLlama 3.3 70Bを使用

---

#### FCM

**正式名称**: Firebase Cloud Messaging

**意味**: Googleが提供するプッシュ通知サービス

**本プロジェクトでの使用**: アプリ閉鎖中のユーザーへのプッシュ通知

---

#### API

**正式名称**: Application Programming Interface

**意味**: ソフトウェア間の通信インターフェース

**本プロジェクトでの使用**: RESTful APIとしてバックエンドサービスを提供
