---
name: create-pr
description: 現在のブランチの変更からPull Requestを作成する。「PR作って」「Pull Request 作成」と言われた時に使用。変更分析→テンプレート選択→PR作成→ラベル適用→自動レビュー。
---

# Pull Request Creation スキル

現在のブランチの変更内容を分析し、GitHub Pull Requestを作成するスキルです。

## 入力契約

- 引数なし。現在のブランチを対象に動作する
- `main` / `master` ブランチにいる場合はエラーハンドリング表に従い中止する

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

判定ルールは `../../rules/label-definitions.md` を参照。

- **関連Issueがある場合**: Issue のラベルを継承（最優先）。以下で取得する:

  ```bash
  gh issue view <Issue番号> --json labels --jq '.labels[].name'
  ```

- **Issueがない場合**: コミットプレフィックスの頻度から判定。`test:` / `chore:` / `style:`（UI/UX 以外の用途）はカウント対象外。

### ステップ4: テンプレートの適用

判定された種類に応じてテンプレートを選択し、プレースホルダ（`[...]`）を取得値や具体的内容で置換する:

- **bug** → `./assets/templates/bug.md`
- **enhancement** → `./assets/templates/enhancement.md`
- **refactor** → `./assets/templates/refactor.md`
- **ui/ux** → `./assets/templates/ui-ux.md`
- **documentation** → `./assets/templates/documentation.md`

Issue 連携がない場合は本文の `## 関連Issue` 節内容を `なし` に置換し、`Closes #[Issue番号]` 行は削除する。

### ステップ5: リモートへの push

ブランチが未 push or リモートと差分がある場合のみ push する:

```bash
# 追跡ブランチの有無を確認
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "no-upstream"

# 未 push なら
git push -u origin <現在のブランチ名>
```

### ステップ6: PR作成

ラベルは `--label` で同時に指定する。PR 番号は出力から `--json` で抽出して後続ステップで使う:

```bash
PR_URL=$(gh pr create \
  --base main \
  --title "<PRタイトル>" \
  --body "$(cat <<'EOF'
<ステップ4で生成した PR 本文>
EOF
)" \
  --label "<ラベル>")

PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+$')
```

### ステップ7: 自動レビュー

Agent tool で pr-reviewer サブエージェントを起動:

- subagent_type: `pr-reviewer`
- prompt: 「Pull Request #${PR_NUMBER} をレビューしてください。ラベルは <ラベル名> です。」

ラベルを渡すことで、エージェントがラベルに応じた専門スペシャリストの観点でレビューを実施します。

## 出力契約

`gh pr create` の出力 URL 末尾から PR 番号を抽出し、以下のフォーマットで報告する:

```
✅ PR #[番号]を作成しました。

タイトル: [PRタイトル]
種類: [bug/enhancement/ui/ux/documentation/refactor]
関連Issue: #[Issue番号] または なし
URL: [GitHub PR URL]

レビュー待ちです。
```

## 完了条件

- Pull Request が正常に作成される
- 関連 Issue がある場合は紐付け完了
- ラベルに対応するテンプレートが適用される
- 自動レビュー（pr-reviewer agent）が GitHub に投稿される

## PRタイトルの生成

コミットプレフィックスの詳細は `../../rules/commit-conventions.md` を参照。

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

| 症状               | 対処                               |
| ------------------ | ---------------------------------- |
| mainブランチにいる | 新しいブランチを作成するよう案内   |
| 変更がない         | コミットしてから再実行するよう案内 |
| コンフリクトがある | 競合ファイルを表示し解決を促す     |
