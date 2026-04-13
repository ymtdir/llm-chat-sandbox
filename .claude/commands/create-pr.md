---
description: 現在のブランチからPull Requestを作成。変更分析→PR本文生成→ラベル適用→自動レビュー。
---

# Pull Request作成

このコマンドは、現在のブランチの変更内容を分析し、適切なテンプレートでPRを作成します。

## 実行方法

```bash
claude
> /create-pr
```

## 手順

### ステップ1: ブランチと変更内容の確認

1. 現在のブランチ名を確認
2. 関連するIssue番号を特定（ブランチ名から）
3. コミット履歴を分析

### ステップ2: pr-creationスキルの実行

1. **pr-creationスキル**をロード
2. スキルが以下を自動実行:
   - 変更内容の分析
   - 関連Issueの確認
   - PRテンプレートの選択（bug/feature/refactor）
   - PR本文の生成
   - GitHub APIでPR作成
   - 自動レビューの実行とGitHub投稿

### ステップ3: 結果の報告

PR作成後の情報を表示:

```
✅ Pull Requestを作成しました！

PR #[番号]: [タイトル]
URL: https://github.com/[owner]/[repo]/pull/[番号]
関連Issue: #[Issue番号]

マージの準備:
- レビュー依頼: gh pr review --request @reviewer
- 自動マージ: gh pr merge --auto
```

## 完了条件

- Pull Requestが正常に作成される
- 関連Issueとの紐付けが完了
- 適切なテンプレートが適用される
- 自動レビューがGitHubに投稿される

完了時のメッセージ:

```
「PR #[番号]を作成しました。

タイトル: [PRタイトル]
種類: [bug/feature/refactor]
関連Issue: #[Issue番号]
URL: [GitHub PR URL]

レビュー待ちです。」
```
