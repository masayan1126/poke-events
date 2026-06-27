---
name: pokeca-site-generate
description: Generate and validate the poke-events GitHub Pages HTML from a filtered Pokemon Card event JSON with required action plans. Use when refreshing index.html, preparing a Pages deploy, or automating site generation for this repository.
---

Read `references/site-generation.md`, then run the deterministic wrapper from the repo root:

```bash
python3 scripts/generate_site.py <events.json>
```

When the user asks to run this automation, continue through site reflection after validation: stage explicit changed files, commit, and push to `main` so the existing GitHub Pages workflow publishes the site. Stop before commit/push only for review-only, no-publish, no-push, or dry-run requests.
