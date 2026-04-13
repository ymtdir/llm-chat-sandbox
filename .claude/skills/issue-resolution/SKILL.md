---
name: issue-resolution
description: GitHub Issueをブランチ作成・原子的コミットで解決する。/resolve-issueコマンドから使用。
---

# Issue Resolution スキル

GitHub Issueの内容を読み取り、適切なブランチで解決を行うスキルです。

## 解決プロセス

### ステップ1: Issue解析

```bash
gh issue view [番号]
gh issue view [番号] --comments
```

Issueの種類を判定：

- **bug**: 修正とテスト追加
- **enhancement**: 新機能の追加
- **refactor**: コード改善

### ステップ2: ブランチ作成

```bash
git checkout -b issue-[番号]-[簡潔な説明]
```

### ステップ3: 作業単位での解決

**重要: 各タスクごとに即座にコミット**

コミット規約は `../rules/commit-conventions.md` に従う。

```bash
# タスク1完了 → 即コミット
git add [変更ファイル]
git commit -m "feat: [変更内容]"

# タスク2完了 → 即コミット
git add [変更ファイル]
git commit -m "test: [テスト内容]"
```

### ステップ4: 品質チェック

全タスク完了後にテスト・lint・型チェック等を実行します。
プロジェクトの技術スタックに応じたコマンドを使用してください。

## エラーハンドリング

| 症状 | 対処 |
| ---- | ---- |
| Issueが見つからない | GitHub権限を確認 |
| 既存ブランチがある | 別名で作成するか既存を使用するか確認 |
| テスト失敗 | 失敗内容を表示し修正を促す |
