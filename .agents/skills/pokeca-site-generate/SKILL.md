---
name: pokeca-site-generate
description: Generate and validate the poke-events GitHub Pages HTML from a filtered Pokemon Card event JSON with required action plans. Use when refreshing index.html, preparing a Pages deploy, or automating site generation for this repository.
---

Read `references/site-generation.md`, then run the deterministic wrapper from the repo root:

```bash
python3 scripts/generate_site.py <events.json>
```

Do not push or deploy unless the user explicitly asks in the same turn.
