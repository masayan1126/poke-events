# poke-events Codex Guide

## Objective

This repository publishes a static GitHub Pages site for Pokemon Card event recommendations. Codex should automate the site-generation step from a collected event JSON into `index.html`, then reflect the validated site by using the existing GitHub Pages workflow on `main`.

## Site Generation Workflow

1. Use the repo skill `$pokeca-site-generate` when the task is to generate or refresh the site.
2. Start from an event JSON that already contains filtered events and 3-4 action plans.
3. Run `python3 scripts/generate_site.py <events.json>` from the repository root.
4. Confirm `scripts/validate_event_json.py` and `scripts/validate_generated_site.py` both pass.
5. Review the generated `index.html` diff before committing.
6. When the user asks to run this automation, continue through site reflection without stopping: stage explicit changed files, commit, and push to `main` so the existing GitHub Pages workflow publishes the site. Stop before commit/push only when the user explicitly says review only, do not publish, do not push, or asks for a dry run.
   - Reason: The user approved this automation to run nonstop through site reflection.
   <!-- added: 2026-06-27 -->
7. After the GitHub Pages workflow succeeds, open `https://masayan1126.github.io/poke-events/` in the browser and verify the rendered page, not only the HTML source. Confirm there are no console errors and that the page shows event cards and 3-4 plan cards for the target date/area before reporting completion.
   <!-- added: 2026-06-30 -->

## Hard Gates

- Never generate or deploy when `plans` is empty.
- `plans` must contain 3-4 plans.
- Each plan must include `id`, `name`, `subtitle`, `rating`, `steps`, and `merit`.
- Each plan step must include `time`, `event`, `venue`, and `area`; include `url` when a Players Club detail URL is available.
- When any candidate event or recommended plan uses GIRAFULLなんば店, check https://x.com/GIRAFULL_Namba for the target month's event schedule post, inspect the attached schedule image carefully, and record the target day's floor and label color in `venue_checks.girafull_namba_x`.
- For the favorite shops `おじゃま館蒲生店`, `あっぷる 今福店`, `カードショップきりん 大阪天満橋店`, and `トレカWIN`, include `favorite_shop_filters` entries that state capacity/participant-count conditions and other filter criteria such as time, availability, and travel burden.
- Keep `.github/workflows/deploy.yml` as the deployment surface. The generation automation should update site files, not bypass GitHub Pages.
- For site reflection, use the GitHub Pages workflow by pushing the validated commit; do not use any separate deployment path.
- Do not call the automation complete after push alone. The final gate is browser-visible verification of the live GitHub Pages URL, including rendered event cards, rendered action plans, and no blocking JavaScript console errors.

## Agent Roles

- Planner: identify the input JSON, target output, and whether deployment is requested.
- Generator: run the site-generation command and inspect the generated diff.
- Evaluator: run validation and flag missing plans, malformed event data, or broken HTML before the user sees the result.
