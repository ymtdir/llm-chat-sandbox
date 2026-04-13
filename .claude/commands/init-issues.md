---
description: /setup-project完了後に初期開発Issue群を一括作成。プロジェクトドキュメントを分析し依存関係付きIssueセットを生成。
---

# 初期Issue一括作成

プロジェクトの開発を開始するための基本的なIssueセットを作成します。

## 前提条件

- `/setup-project`が完了していること
- 以下のドキュメントが存在すること：
  - docs/requirements.md
  - docs/basic-design.md
  - docs/detailed-design.md
  - docs/development-guide.md

## 手順

### ステップ1: プロジェクト分析

1. 4つのドキュメントを全て読み込む
2. プロジェクトタイプと技術スタックを確認
3. 主要機能を抽出

### ステップ2: Issue作成計画

プロジェクトに応じた標準Issueセットを設計：

- 開発環境セットアップ
- 基本プロジェクト構造
- データモデル実装
- プロジェクト固有の機能Issue

各Issueについて以下を決定：

- タイトルと本文
- 種類（bug/enhancement/refactor/documentation）
- 依存関係（前のステップへの依存を明記）

### ステップ3: issue-creationスキルで各Issueを作成

**issue-creationスキル**をロードし、計画した各Issueを順番に作成します。

**重要**: ラベル判定・テンプレート適用のロジックはissue-creationスキルに一元化されているため、このコマンドでは独自にラベルを決定しない。

### ステップ4: 結果レポート

```
✅ 初期Issue作成完了！

作成されたIssue:
#7 【Step 1】開発環境セットアップ (enhancement)
#8 【Step 2】基本プロジェクト構造 (enhancement)
#9 【Step 3】データモデル実装 (enhancement)
...

次のステップ:
/resolve-issue 7  # 開発を開始
```
