# GitHubラベル定義

## 必須参照ドキュメント

**GitHub Issue/PR作成時は必ずこのファイルを参照すること**

## 適用範囲

このラベル定義は以下のすべてのコマンド/スキルで**必須**です：

- `/init-issues` - 初期Issue一括作成
- `/create-issue` - Issue作成
- `/create-pr` - Pull Request作成
- `issue-creation` スキル
- `pr-creation` スキル
- その他、GitHub Issue/PRを作成するすべての操作

## 標準ラベル

### bug 🐛

- **用途**: バグ・不具合・エラーの修正
- **キーワード**: error, bug, broken, fail, crash, fix, 動作しない, 修正, エラー, バグ
- **コミットプレフィックス**: `fix:`
- **優先順位**: 1（最優先）
- **色**: #d73a4a（赤）

### enhancement ✨

- **用途**: 新機能・機能改善
- **キーワード**: 追加, 改善, 機能, enhancement, feature, feat, 新機能
- **コミットプレフィックス**: `feat:`
- **優先順位**: 2
- **色**: #a2eeef（水色）

### ui/ux 🎨

- **用途**: UI/UXの変更・スタイル調整
- **キーワード**: UI, UX, style, デザイン, 見た目, レイアウト, CSS
- **コミットプレフィックス**: `style:`
- **優先順位**: 3
- **色**: #7057ff（紫）

### documentation 📚

- **用途**: ドキュメントの作成・更新
- **キーワード**: ドキュメント, README, 説明, docs, documentation
- **コミットプレフィックス**: `docs:`
- **優先順位**: 4
- **色**: #0075ca（青）

### refactor ♻️

- **用途**: コード品質改善・リファクタリング・パフォーマンス改善
- **キーワード**: リファクタ, refactor, 整理, 技術的負債, TODO, FIXME, performance, 高速化, 最適化, optimize
- **コミットプレフィックス**: `refactor:`
- **優先順位**: 5
- **色**: #cfd3d7（灰）

## 判定ルール

### Issue作成時（issue-creation）

1. タイトルと本文のキーワードをチェック
2. 複数のキーワードがマッチした場合、優先順位の高いラベルを採用
3. マッチしない場合は `enhancement` をデフォルト

### PR作成時（pr-creation）

1. 関連Issueのラベルがあれば継承（最優先）
2. コミットプレフィックスの頻度で判定
3. 同数の場合は優先順位で決定

### 初期Issue作成時（init-issues）

典型的な開発ステップとラベルの対応：

- 環境構築・セットアップ → `enhancement`
- プロジェクト構造・アーキテクチャ → `enhancement`
- UI/画面実装・スタイリング → `ui/ux`
- カレンダー/ダッシュボード等のUI → `ui/ux`
- アニメーション・ビジュアル要素 → `ui/ux`
- 機能実装（CRUD, API連携等） → `enhancement`
- データベース・状態管理 → `enhancement`
- テスト環境・CI/CD → `refactor`
- コード品質改善 → `refactor`
- ドキュメント・README → `documentation`
- バグ修正（あれば） → `bug`

## ラベル付与対象外

以下のコミットプレフィックスは自動ラベル付与しない：

- `test:` - テストコード
- `chore:` - 雑務・メンテナンス

## 推奨コミットメッセージ例

```bash
# パフォーマンス改善はrefactor:を使用
refactor: データベースクエリを最適化して処理速度を改善
refactor: 画像読み込みのパフォーマンスを向上

# その他の例
feat: ユーザー認証機能を追加
fix: ログイン時のセッションエラーを修正
style: ヘッダーのレイアウトを改善
docs: APIドキュメントを更新
```

## 注意事項

### ✅ 使用可能なラベル（これだけ）

1. **bug** 🐛
2. **enhancement** ✨
3. **ui/ux** 🎨
4. **documentation** 📚
5. **refactor** ♻️

**これ以外のラベルは絶対に使用しないこと**
