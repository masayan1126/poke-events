# poke-events ポケカ イベントページ

## Codex移行後のサイト生成ワークフロー
Codexでは `AGENTS.md` と `.agents/skills/pokeca-site-generate/` を主な指示面として使う。

1. イベント収集・フィルタリング済みJSONを用意する
2. **行動プラン生成（必須）** — plans[] を空にしてはいけない。3〜4プランを必ず生成してから JSON に含める
3. `$pokeca-site-generate` スキル、または `python3 scripts/generate_site.py <events.json>` でHTML生成・検証を行う
4. GitHub Pagesデプロイは `main` へのpush後に `.github/workflows/deploy.yml` が実行する

## 行動プランの必須条件
- `plans: []` のまま deploy してはいけない
- プランはイベントデータ取得後、デプロイ前に生成する
- プランの形式は `.agents/skills/pokeca-site-generate/references/site-generation.md` 参照

## ブラウザデータ取得のtips
- Players Club はCSR（クライアントサイドレンダリング）のため fetch でHTMLからデータ取得不可
- localStorage を使って複数ページ跨ぎのデータ蓄積が有効（同一オリジン間で引き継がれる）
- ツール出力が truncate される場合はフィールド別・インデックス範囲別に分割取得する
