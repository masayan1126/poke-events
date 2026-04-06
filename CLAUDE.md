# poke-events ポケカ イベントページ

## デプロイワークフロー（必須順序）
1. `pokeca-event` スキル — イベント収集・フィルタリング・JSON生成
2. **行動プラン生成（必須）** — plans[] を空にしてはいけない。3〜4プランを必ず生成してから JSON に含める
3. `pokeca-event-deploy` スキル — HTML生成・GitHub Pagesデプロイ

## 行動プランの必須条件
- `plans: []` のまま deploy してはいけない
- プランはイベントデータ取得後、デプロイ前に生成する
- プランの形式は `.claude/skills/pokeca-event/REFERENCE.md` の Step 5 参照

## ブラウザデータ取得のtips
- Players Club はCSR（クライアントサイドレンダリング）のため fetch でHTMLからデータ取得不可
- localStorage を使って複数ページ跨ぎのデータ蓄積が有効（同一オリジン間で引き継がれる）
- ツール出力が truncate される場合はフィールド別・インデックス範囲別に分割取得する
