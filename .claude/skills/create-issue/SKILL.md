---
name: create-issue
description: 開発中に発見した課題をGitHub Issueとして作成する。「Issue作って」「課題をIssue化」と言われた時、または init-issues skill から使用。bug/enhancement/ui/ux/documentation/refactor に分類しラベルを適用。
---

# Issue Tracking スキル

開発中に発見した課題をGitHub Issueとして記録するスキルです。

## 入力契約

- **課題説明**: 必須。ユーザーが入力した自由文をそのまま課題説明として扱う
- オプションフラグ（`--type` など）は受け付けない（種類判定は本 skill が行う）

## Issue作成プロセス

### ステップ1: 課題の分析と分類

課題の内容からラベルを自動判定します。
判定ルールの詳細は `../../rules/label-definitions.md` を参照してください。

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

選択されたラベルに対応するテンプレートを読み込み、情報を埋め込みます。ステップ2で取得した `branch` / `latest commit` は、テンプレ末尾の `## コンテキスト` 節にそのまま転記する。

- **bug** → `assets/templates/bug.md`
- **enhancement** → `assets/templates/enhancement.md`
- **refactor** → `assets/templates/refactor.md`
- **ui/ux** → `assets/templates/ui-ux.md`
- **documentation** → `assets/templates/documentation.md`

プレースホルダ（`[...]` で囲われた箇所）は取得値や具体的な内容で置換する。該当情報が無い欄は `N/A` と記す（欄ごと削除しない）。

### ステップ4: GitHub Issue作成

`gh issue create` を以下の雛形で実行する。タイトルは課題の要点を 1 行・50 文字以内で表現し、接頭辞（`[bug]` など）は付けない。

```bash
gh issue create \
  --title "<課題タイトル>" \
  --label "<ラベル名>" \
  --body "$(cat <<'EOF'
<ステップ3 で生成した Issue 本文>
EOF
)"
```

`--assignee` / `--milestone` / `--project` 等はユーザーから明示指示があった場合のみ追加する。

## 出力契約

処理完了時、Issue 作成の出力 URL 末尾から Issue 番号を抽出し、以下のフォーマットで報告する:

```
✅ Issue #[番号]を作成しました。

タイトル: [課題タイトル]
種類: [bug/enhancement/ui/ux/documentation/refactor]
URL: [GitHub Issue URL]

現在の作業を続けてください。
```

init-issues skill など別 skill から呼ばれる場合は、呼び出し元が独自の集約レポートを出すため、この節の出力は省略して Issue 番号のみを返してよい。

## エラーハンドリング

### GitHub 認証エラー / 未設定の場合

`gh auth status` が未認証エラーを返した場合、以下の両方を行う:

1. Issue 内容をリポジトリルート直下にローカル保存する:

   ```
   Write('<repo-root>/.issues-pending/<YYYY-MM-DD>-<slug>.md', <Issue 内容>)
   ```

   - `<YYYY-MM-DD>` は保存日（例: `2026-04-21`）
   - `<slug>` は Issue タイトルを英小文字 + ハイフン区切りに変換（日本語・スペース・スラッシュは除去または置換）
   - ファイル先頭に `# <タイトル>` と `labels: <ラベル名>` を付与し、ステップ3 の本文を続ける

2. ユーザーに `gh auth status` で認証状態を確認し、再認証後に保存ファイルを元に Issue 作成するよう案内する。

## トラブルシューティング

| 症状 | 原因 | 対処 |
| ---- | ---- | ---- |
| Issue作成がエラー | GitHub未認証 | `gh auth status`で確認、再認証 |
| ラベルが付与されない | リポジトリにラベルが未作成 | GitHubのLabels設定を確認 |
| Issue分類が不適切 | キーワードマッチの曖昧さ | ユーザーに種類を確認してから作成 |
