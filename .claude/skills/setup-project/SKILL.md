---
name: setup-project
description: プロジェクトの 4 ドキュメント（要件定義書・基本設計書・詳細設計書・開発ガイドライン）を対話的に一括作成する。「プロジェクトの初回セットアップ」「4ドキュメント作って」と言われた時に使用。各ステップでユーザー承認を得てから次に進む。
---

# 初回プロジェクトセットアップスキル

プロジェクトの 4 つの永続ドキュメントを対話的に作成するスキルです。各ステップでユーザーの承認を得てから次のドキュメントに進みます。

## 実行前の確認

以下のパスの存在を確認し、ユーザーに状況を提示する:

- `docs/ideas/` 配下のアイデアメモ
- 4 つの成果物: `docs/requirements.md` / `docs/basic-design.md` / `docs/detailed-design.md` / `docs/development-guide.md`

### 既存ドキュメント検出時のフロー

4 成果物のいずれかが既に存在する場合、ユーザーに以下の選択肢を提示してから該当ステップに進む:

- **(A) 再利用（skip）**: 既存ファイルをそのまま次ステップの入力として使う
- **(B) 更新**: 該当 skill の「既存ドキュメント更新時の整合判断」節に従って差分更新する
- **(C) 再作成**: 既存を破棄して新規作成（承認必須、`<file>.bak` に退避推奨）

## 手順

### ステップ1: 要件定義書の作成

1. **requirements-definition skill** を呼び出し、`docs/requirements.md` を作成（または (A)/(B)/(C) に従って処理）
2. skill 内部で `docs/ideas/*.md` の有無を判定し、空なら対話形式ヒアリングに切り替える（skill 側で処理）
3. ユーザーに確認を求め、**承認されるまで待機**

### ステップ2: 基本設計書の作成

1. **basic-design skill** を呼び出し、`docs/basic-design.md` を作成（または (A)/(B)/(C) に従って処理）
2. ユーザーに確認を求め、**承認されるまで待機**

### ステップ3: 詳細設計書の作成

1. **detailed-design skill** を呼び出し、`docs/detailed-design.md` を作成（または (A)/(B)/(C) に従って処理）
2. ユーザーに確認を求め、**承認されるまで待機**

### ステップ4: 開発ガイドラインの作成

1. **development-guide skill** を呼び出し、`docs/development-guide.md` を作成（または (A)/(B)/(C) に従って処理）
2. ユーザーに確認を求め、**承認されるまで待機**

## 完了条件

4 つの永続ドキュメントが全て作成されていること。

完了時のメッセージ:

```
✅ 初回セットアップが完了しました。

作成したドキュメント:
- docs/requirements.md
- docs/basic-design.md
- docs/detailed-design.md
- docs/development-guide.md

これで開発を開始する準備が整いました。

今後の使い方:
- ドキュメントの編集: 普通に会話で依頼
  例: 「要件定義書に新機能を追加して」
- 初期Issue 一括作成: init-issues skill
- 新機能追加（Issue駆動）: create-issue → resolve-issue → create-pr の各 skill
- ドキュメントレビュー: review-doc skill に対象パスを渡す
```
