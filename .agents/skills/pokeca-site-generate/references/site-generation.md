# Site Generation Reference

## Workflow

1. Identify the event JSON path.
2. Confirm the JSON already contains filtered events and 3-4 action plans.
3. Run `python3 scripts/generate_site.py <events.json>` from the repository root.
4. Review the generated `index.html` diff.
5. If the user asked to run this automation, continue through site reflection without pausing: stage explicit changed files, commit, and push to `main`.
6. Report validation results, changed files, commit, and push status.

Stop before commit/push only when the user explicitly says review only, do not publish, do not push, or dry run.
Why: The user approved this automation to run nonstop through site reflection, and GitHub Pages publication is triggered by the existing workflow on `main`.
<!-- added: 2026-06-27 from user feedback -->

Use `--require-future-target` when generating a live page for publication. Skip that flag only for local regression tests with historical fixtures.

## Input Contract

Required top-level keys:

- `meta`
- `events`
- `plans`

Required `meta` keys:

- `report_date`
- `target_date`
- `area`

Supported event category keys:

- `gym_battle`
- `open_league`
- `friend_battle`
- `self_event`

Each event should include `datetime`, `name`, `venue`, and `address`. `fee`, `capacity`, `travel_time`, `url`, and `is_full` are optional but improve the generated cards and tags.

Each plan must include `id`, `name`, `subtitle`, `rating`, `steps`, and `merit`.

Each step must include `time`, `event`, `venue`, and `area`. Include `url` when a Players Club detail URL is available.

Required contextual checks:

- `favorite_shop_filters` must be present for Osaka generation and include entries for `おじゃま館蒲生店`, `あっぷる 今福店`, `カードショップきりん 大阪天満橋店`, and `トレカWIN`.
- Each favorite shop entry must state the capacity or participant-count condition and the filter criteria used, such as time, availability, fee, category, or travel burden.
- When candidate events or action plans include GIRAFULLなんば店, include `venue_checks.girafull_namba_x`.
- `venue_checks.girafull_namba_x` must be based on https://x.com/GIRAFULL_Namba. Check the target month's event schedule post, inspect the attached schedule image carefully because it can be small, and record `account_url`, `schedule_post_url`, `schedule_month`, `target_date`, `floor`, `label_color`, and `summary`.

## Commands

Generate the default site:

```bash
python3 scripts/generate_site.py path/to/events.json
```

Generate a review file:

```bash
python3 scripts/generate_site.py path/to/events.json --output /tmp/poke-events-preview.html
```

Run gates separately:

```bash
python3 scripts/validate_event_json.py path/to/events.json
python3 scripts/generate_page.py path/to/events.json --output index.html
python3 scripts/validate_generated_site.py index.html
```

Reflect the site after validation:

```bash
git add <events.json> index.html scripts/generate_page.py scripts/validate_event_json.py AGENTS.md .agents/skills/pokeca-site-generate/SKILL.md .agents/skills/pokeca-site-generate/references/site-generation.md
git commit -m "Update Pokemon Card event site"
git push origin main
```

Adjust the staged paths to the actual changed files. Do not use `git add .` for this automation.

## Review Checklist

- `plans` has 3-4 items.
- `index.html` has exactly one `const DATA = ...;` block.
- `DATA.areas` and `DATA.dates[].areaData` exist because the current UI depends on them.
- The generated title includes the target date and area.
- Event counts are plausible for the selected area/date.
- Players Club detail links are present when available.
- Favorite shop filter entries are visible in the generated notes.
- GIRAFULLなんば candidates or recommendations include X schedule floor and label color notes.
- If this is a normal automation run, push the validated commit to `main`; skip push only for review-only, no-publish, no-push, or dry-run requests.
