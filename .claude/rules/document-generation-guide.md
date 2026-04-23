# ドキュメント生成ガイド

ドキュメント生成スキル（requirements-definition, basic-design, detailed-design, development-guide）で、メインドキュメントを生成する際のフォーマット・制約について定めます。

## 既存ドキュメント最優先

`docs/` に既存ドキュメントがある場合、以下の優先順位に従ってください:

1. **既存のドキュメント (`docs/[ファイル名].md`)** - 最優先
   - プロジェクト固有の要件が記載されている
   - このスキルのガイドより優先する
   - 既存の節構造・表記・言語をそのまま維持して更新する

2. **このスキルのガイド** - 参考資料
   - 汎用的なテンプレートと例
   - 既存ドキュメントがない場合、または補足として使用

### 新規作成時と更新時の使い分け

- **新規作成時**: 各 skill 配下のテンプレート（`./assets/template.md`）および参照ガイド（`./references/` 配下）を使用
- **更新時**: 既存ドキュメントの構造と内容を維持しながら更新（template の強制適用はしない）

## 出力制約

各スキルのメインドキュメントは以下の制約に従ってください：

- **行数制限**: 上限目安 400 行（下限なし、簡潔優先）
- **分割トリガー**: メインドキュメントが 400 行を超える見込みの場合、詳細部分をサブディレクトリに分割する
- **参照記法**: メイン側はサマリ 3-5 行 + 具体ファイルへのリンクを置く

```markdown
# 例: docs/requirements.md 内での参照

## 主要機能

- 機能A（ユーザー管理）
- 機能B（レポート生成）

詳細な機能要件・受け入れ条件は [docs/requirements/features.md](./requirements/features.md) を参照してください。
```

## メインドキュメント

```
docs/requirements.md       # 要件定義書
docs/basic-design.md       # 基本設計書
docs/detailed-design.md    # 詳細設計書
docs/development-guide.md  # 開発ガイドライン
```

## 補足ドキュメント（サブディレクトリ）

400 行超過時は skill ごとに専用サブディレクトリに分割し、衝突を避ける:

| skill | 分割先サブディレクトリ |
|---|---|
| requirements-definition | `docs/requirements/` |
| basic-design | `docs/basic-design/` |
| detailed-design | `docs/detailed-design/` |
| development-guide | `docs/development-guide/` |

例:

```
docs/requirements/features.md
docs/requirements/acceptance-criteria.md

docs/basic-design/architecture-detail.md
docs/basic-design/infrastructure.md

docs/detailed-design/api-design.md
docs/detailed-design/db-schema.md

docs/development-guide/implementation-patterns.md
docs/development-guide/glossary.md
```

メインドキュメント内では **節単位で分割**し、「詳細は [docs/xxx/yyy.md](./xxx/yyy.md) を参照」のようにマークダウンリンクで参照する。