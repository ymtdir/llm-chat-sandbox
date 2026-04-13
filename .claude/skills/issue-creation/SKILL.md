---
name: issue-creation
description: 開発中に発見した課題をGitHub Issueとして作成する。/create-issueや/init-issuesから使用。bug/enhancement/refactorに分類しラベルを適用。
---

# Issue Tracking スキル

開発中に発見した課題をGitHub Issueとして記録するスキルです。

## Issue作成プロセス

### ステップ1: 課題の分析と分類

課題の内容からラベルを自動判定します。
判定ルールの詳細は `../rules/label-definitions.md` を参照してください。

判定方法：

1. タイトルと本文からキーワードを検索
2. マッチしたキーワードに基づいてラベルを選択
3. 複数マッチした場合は優先順位（bug > enhancement > ui/ux > documentation > refactor）で決定

### ステップ2: コンテキスト情報の収集

```bash
git branch --show-current
git log -1 --oneline
```

### ステップ3: テンプレートの適用

選択されたテンプレートを読み込み、情報を埋め込み：

- **bug** → `assets/templates/bug.md`
- **enhancement** → `assets/templates/enhancement.md`
- **refactor** → `assets/templates/refactor.md`
- **documentation** → シンプルな説明形式

### ステップ4: GitHub Issue作成

`gh issue create`コマンドでIssueを作成します。

## エラーハンドリング

### GitHub未設定の場合

ローカルファイルとして保存：

```bash
Write('.issues-pending/[日時]-[タイトル].md', [Issue内容])
```

### 認証エラーの場合

`gh auth status`で確認するよう案内。

## トラブルシューティング

| 症状 | 原因 | 対処 |
| ---- | ---- | ---- |
| Issue作成がエラー | GitHub未認証 | `gh auth status`で確認、再認証 |
| ラベルが付与されない | リポジトリにラベルが未作成 | GitHubのLabels設定を確認 |
| Issue分類が不適切 | キーワードマッチの曖昧さ | ユーザーに種類を確認してから作成 |
