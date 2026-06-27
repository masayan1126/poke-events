# poke-events Codex Guide

## Objective

This repository publishes a static GitHub Pages site for Pokemon Card event recommendations. Codex should automate the site-generation step from a collected event JSON into `index.html`, then leave deployment to the existing GitHub Pages workflow on `main`.

## Site Generation Workflow

1. Use the repo skill `$pokeca-site-generate` when the task is to generate or refresh the site.
2. Start from an event JSON that already contains filtered events and 3-4 action plans.
3. Run `python3 scripts/generate_site.py <events.json>` from the repository root.
4. Confirm `scripts/validate_event_json.py` and `scripts/validate_generated_site.py` both pass.
5. Review the generated `index.html` diff before committing.
6. Do not deploy or push unless the user explicitly asks for it in that turn.

## Hard Gates

- Never generate or deploy when `plans` is empty.
- `plans` must contain 3-4 plans.
- Each plan must include `id`, `name`, `subtitle`, `rating`, `steps`, and `merit`.
- Each plan step must include `time`, `event`, `venue`, and `area`; include `url` when a Players Club detail URL is available.
- Keep `.github/workflows/deploy.yml` as the deployment surface. The generation automation should update site files, not bypass GitHub Pages.

## Agent Roles

- Planner: identify the input JSON, target output, and whether deployment is requested.
- Generator: run the site-generation command and inspect the generated diff.
- Evaluator: run validation and flag missing plans, malformed event data, or broken HTML before the user sees the result.
