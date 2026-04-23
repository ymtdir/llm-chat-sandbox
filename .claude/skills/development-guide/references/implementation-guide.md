# 実装ガイド

コーディング規約と実装パターンのガイドです。プロジェクトの言語・フレームワークに応じてカスタマイズしてください。

## 命名規則

### 変数・関数

```typescript
// 変数: camelCase、名詞
const userName = 'John';
const isCompleted = true;

// 関数: camelCase、動詞で始める
function fetchUserData() {}
function validateEmail(email: string) {}

// Boolean: is, has, should, canで始める
const isValid = true;
const hasPermission = false;
```

### クラス・インターフェース・型

```typescript
// クラス: PascalCase、名詞
class UserAuthenticationService {}

// インターフェース: PascalCase
interface UserProfile {}

// 型エイリアス: PascalCase
type OrderStatus = 'pending' | 'confirmed' | 'shipped';
```

### 定数

```typescript
// UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';
```

### ファイル名

- クラスファイル: PascalCase（例: `UserService.ts`）
- 関数ファイル: camelCase（例: `formatDate.ts`）
- 定数ファイル: kebab-case（例: `api-endpoints.ts`）

## 関数設計

### 単一責務の原則

```typescript
// ✅ 良い例: 単一の責務
function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

function formatPrice(amount: number): string {
  return `¥${amount.toLocaleString()}`;
}

// ❌ 悪い例: 複数の責務
function calculateAndFormatPrice(items: CartItem[]): string {
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return `¥${total.toLocaleString()}`;
}
```

### 関数の長さとパラメータ

- 目標: 20行以内、推奨: 50行以内
- パラメータが3つ以上ならオブジェクトにまとめる

```typescript
// ✅ 良い例: オブジェクトでまとめる
interface CreateUserInput {
  name: string;
  email: string;
  role?: 'admin' | 'member';
}

function createUser(input: CreateUserInput): User {}
```

## エラーハンドリング

### カスタムエラークラス

```typescript
class ValidationError extends Error {
  constructor(message: string, public field: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

class NotFoundError extends Error {
  constructor(public resource: string, public id: string) {
    super(`${resource} not found: ${id}`);
    this.name = 'NotFoundError';
  }
}
```

### エラーハンドリングパターン

```typescript
// ✅ 良い例: 適切なエラーハンドリング
async function getUser(id: string): Promise<User> {
  try {
    const user = await repository.findById(id);
    if (!user) throw new NotFoundError('User', id);
    return user;
  } catch (error) {
    if (error instanceof NotFoundError) {
      logger.warn(`ユーザーが見つかりません: ${id}`);
      throw error;
    }
    throw new DatabaseError('ユーザーの取得に失敗しました', error as Error);
  }
}

// ❌ 悪い例: エラーを無視
async function getUser(id: string): Promise<User | null> {
  try {
    return await repository.findById(id);
  } catch (error) {
    return null; // エラー情報が失われる
  }
}
```

### エラーメッセージ

```typescript
// ✅ 良い例: 具体的で解決策を示す
throw new ValidationError('タイトルは1-200文字で入力してください。現在: 250文字', 'title');

// ❌ 悪い例: 曖昧
throw new Error('Invalid input');
```

## 非同期処理

```typescript
// ✅ 良い例: async/awaitを使用
async function fetchUserOrders(userId: string): Promise<Order[]> {
  const user = await userRepository.findById(userId);
  return orderRepository.findByUserId(user.id);
}

// ✅ 良い例: Promise.allで並列実行
async function fetchMultipleUsers(ids: string[]): Promise<User[]> {
  return Promise.all(ids.map(id => userRepository.findById(id)));
}
```

## コメント規約

### 良いコメント

```typescript
// ✅ 理由を説明
// キャッシュを無効化して最新データを取得
cache.clear();

// ✅ 複雑なロジックを説明
// Kadaneのアルゴリズムで最大部分配列和を計算（O(n)）
let maxSoFar = arr[0];

// ✅ TODO・FIXMEを活用
// TODO: キャッシュ機能を実装 (Issue #123)
// FIXME: 大量データでパフォーマンス劣化 (Issue #456)
```

### 悪いコメント

```typescript
// ❌ コードの内容を繰り返すだけ
// iを1増やす
i++;

// ❌ コメントアウトされたコード
// const oldImplementation = () => { ... };  // 削除すべき
```

## セキュリティ

### 入力検証

```typescript
// ✅ 良い例: 厳密な検証
function validateEmail(email: string): void {
  if (!email || typeof email !== 'string') {
    throw new ValidationError('メールアドレスは必須です', 'email');
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('メールアドレスの形式が不正です', 'email');
  }
}
```

### 機密情報の管理

```typescript
// ✅ 良い例: 環境変数から読み込み
const apiKey = process.env.API_KEY;
if (!apiKey) throw new Error('API_KEY環境変数が設定されていません');

// ❌ 悪い例: ハードコード
const apiKey = 'sk-1234567890abcdef';
```

## パフォーマンス

```typescript
// ✅ 良い例: Mapで O(1) アクセス
const userMap = new Map(users.map(u => [u.id, u]));
const user = userMap.get(userId);

// ❌ 悪い例: 配列で O(n) 検索
const user = users.find(u => u.id === userId);
```

## リファクタリング

### マジックナンバーの排除

```typescript
// ✅ 良い例: 定数を定義
const MAX_RETRY_COUNT = 3;
const RETRY_DELAY_MS = 1000;

// ❌ 悪い例: マジックナンバー
for (let i = 0; i < 3; i++) { await sleep(1000); }
```

### 関数の抽出

```typescript
// ✅ 良い例: 関数を抽出して責務を分離
function processOrder(order: Order): void {
  validateOrder(order);
  calculateTotal(order);
  applyDiscounts(order);
  saveOrder(order);
}
```

## チェックリスト

- [ ] 命名が明確で一貫している
- [ ] 関数が単一の責務を持っている
- [ ] マジックナンバーがない
- [ ] エラーハンドリングが実装されている
- [ ] 入力検証が実装されている
- [ ] 機密情報がハードコードされていない
- [ ] 適切なデータ構造を使用している
