---
description: 課題をGitHub Issueとして作成。種類を分類しテンプレート適用後GitHubに投稿。
---

# 開発中の課題をIssue化

このコマンドは、開発作業中に発見した課題をGitHub Issueとして記録します。

## 手順

### ステップ1: 引数の解析

1. 課題の説明を取得
2. オプションを解析（--type, --priority など）

### ステップ2: issue-creationスキルの実行

1. **issue-creationスキル**をロード
2. スキルに課題内容とオプションを渡してIssue作成

### ステップ3: 結果の報告

```
✅ Issue #[番号]を作成しました。

タイトル: [課題タイトル]
種類: [bug/enhancement/refactor]
URL: [GitHub Issue URL]

現在の作業を続けてください。
```
