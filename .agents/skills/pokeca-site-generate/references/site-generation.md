# Site Generation Reference

## Workflow

1. Identify the event JSON path.
2. Confirm the JSON already contains filtered events and 3-4 action plans.
3. Run `python3 scripts/generate_site.py <events.json>` from the repository root.
4. Review the generated `index.html` diff.
5. Report validation results and changed files.

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

## Review Checklist

- `plans` has 3-4 items.
- `index.html` has exactly one `const DATA = ...;` block.
- `DATA.areas` and `DATA.dates[].areaData` exist because the current UI depends on them.
- The generated title includes the target date and area.
- Event counts are plausible for the selected area/date.
- Players Club detail links are present when available.
- Do not run `git push` unless explicitly requested.
