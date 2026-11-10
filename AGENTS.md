# poke-events（移転済み）

2026-11-10 に、イベント一覧はポケポータル（モノレポ `masayan1126/pokeca` の `apps/portal`、https://pokeportal.msyn.me/events ）へ統合した。このリポジトリはアーカイブ済み。

- 毎週のイベント候補の生成と公開は `/Users/masayan/git/dev/pokeca`（モノレポ）で行う。手順は同リポジトリの `AGENTS.md` と `$pokeca-site-generate` スキル（`.agents/skills/pokeca-site-generate/`）に従う
- このリポジトリのサイト生成（`scripts/generate_site.py`・`src/data/site-data.json`）は使わない。ここへ push しても、GitHub Pages は転送ページ（`redirect/`）しか公開しない
- 過去の収集データ（`data/`）は記録として残している
