---
name: pr-creation
description: 現在のブランチの変更からPull Requestを作成する。/create-prコマンドから使用。変更分析→テンプレート選択→PR作成→ラベル適用→自動レビュー。
---

# Pull Request Creation スキル

現在のブランチの変更内容を分析し、GitHub Pull Requestを作成するスキルです。

## PR作成プロセス

### ステップ1: ブランチ情報の収集

```bash
git branch --show-current
git diff --stat origin/main...HEAD
git log origin/main..HEAD --oneline
git diff --name-only origin/main...HEAD
```

### ステップ2: Issue番号の特定

ブランチ名から自動判定:

- `issue-123-fix-bug` → Issue #123
- その他 → コミットメッセージから`#\d+`を検索

### ステップ3: ラベルの判定

判定ルールは `../rules/label-definitions.md` を参照。

- 関連Issueがある場合 → Issueのラベルを継承（最優先）
- Issueがない場合 → コミットプレフィックスから判定

### ステップ4: テンプレートの適用

判定された種類に応じてテンプレートを選択:

- **bug** → `./assets/templates/bug.md`
- **enhancement** → `./assets/templates/enhancement.md`
- **refactor** → `./assets/templates/refactor.md`
- **documentation** → シンプルなドキュメント更新形式

### ステップ5: PR作成

```bash
gh pr create --title "[PRタイトル]" --body "[テンプレートで生成した本文]" --base main
```

### ステップ6: ラベル付与

```bash
gh pr edit [PR番号] --add-label "[ラベル]"
```

### ステップ7: 自動レビュー

Agent toolでpr-reviewerサブエージェントを起動：

- subagent_type: `pr-reviewer`
- prompt: 「Pull Request #[PR番号]をレビューしてください。ラベルは [ラベル名] です。」

ラベルを渡すことで、エージェントがラベルに応じた専門スペシャリストの観点でレビューを実施します。

## PRタイトルの生成

コミットプレフィックスの詳細は `../rules/commit-conventions.md` を参照。

### Issue連携あり

```
fix: [Issue概要] (#123)
feat: [Issue概要] (#456)
```

### Issue連携なし

```
fix: [主要な変更内容を要約]
feat: [主要な変更内容を要約]
```

## エラーハンドリング

| 症状 | 対処 |
| ---- | ---- |
| mainブランチにいる | 新しいブランチを作成するよう案内 |
| 変更がない | コミットしてから再実行するよう案内 |
| コンフリクトがある | 競合ファイルを表示し解決を促す |
