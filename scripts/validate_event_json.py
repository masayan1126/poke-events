#!/usr/bin/env python3
"""Validate the event JSON contract before generating the static site."""

import argparse
import json
import sys
from datetime import date, datetime


EVENT_CATEGORIES = ("gym_battle", "open_league", "friend_battle", "self_event")
REQUIRED_META = ("report_date", "target_date", "area")
REQUIRED_EVENT_FIELDS = ("datetime", "name", "venue", "address")
REQUIRED_PLAN_FIELDS = ("id", "name", "subtitle", "rating", "steps", "merit")
REQUIRED_STEP_FIELDS = ("time", "event", "venue", "area")


def _is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _parse_yyyy_mm_dd(value):
    if not isinstance(value, str):
        return None
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def validate(data, require_future_target=False):
    errors = []
    warnings = []

    meta = data.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
        meta = {}

    for field in REQUIRED_META:
        if not _is_non_empty_string(meta.get(field)):
            errors.append(f"meta.{field} is required")

    target_date = _parse_yyyy_mm_dd(meta.get("target_date"))
    if meta.get("target_date") and target_date is None:
        errors.append("meta.target_date must be YYYY/MM/DD or YYYY-MM-DD")
    if require_future_target and target_date and target_date < date.today():
        errors.append("meta.target_date must be today or later when --require-future-target is used")

    events = data.get("events")
    if not isinstance(events, dict):
        errors.append("events must be an object")
        events = {}

    total_events = 0
    for category in EVENT_CATEGORIES:
        category_events = events.get(category, [])
        if category_events is None:
            category_events = []
        if not isinstance(category_events, list):
            errors.append(f"events.{category} must be a list")
            continue

        total_events += len(category_events)
        for idx, event in enumerate(category_events, start=1):
            if not isinstance(event, dict):
                errors.append(f"events.{category}[{idx}] must be an object")
                continue
            for field in REQUIRED_EVENT_FIELDS:
                if not _is_non_empty_string(event.get(field)):
                    errors.append(f"events.{category}[{idx}].{field} is required")

    if total_events == 0:
        errors.append("events must contain at least one event across supported categories")

    plans = data.get("plans")
    if not isinstance(plans, list):
        errors.append("plans must be a list")
        plans = []

    if not 3 <= len(plans) <= 4:
        errors.append("plans must contain 3 or 4 action plans before site generation")

    seen_plan_ids = set()
    for idx, plan in enumerate(plans, start=1):
        if not isinstance(plan, dict):
            errors.append(f"plans[{idx}] must be an object")
            continue

        for field in REQUIRED_PLAN_FIELDS:
            if field not in plan:
                errors.append(f"plans[{idx}].{field} is required")

        plan_id = plan.get("id")
        if plan_id is None or not str(plan_id).strip():
            errors.append(f"plans[{idx}].id is required")
        elif plan_id in seen_plan_ids:
            errors.append(f"plans[{idx}].id duplicates another plan")
        else:
            seen_plan_ids.add(plan_id)

        rating = plan.get("rating")
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            errors.append(f"plans[{idx}].rating must be an integer from 1 to 5")

        steps = plan.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"plans[{idx}].steps must be a non-empty list")
            continue

        for step_idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                errors.append(f"plans[{idx}].steps[{step_idx}] must be an object")
                continue
            for field in REQUIRED_STEP_FIELDS:
                if not _is_non_empty_string(step.get(field)):
                    errors.append(f"plans[{idx}].steps[{step_idx}].{field} is required")
            if "url" in step and step["url"] and not str(step["url"]).startswith("https://players.pokemon-card.com/event/detail/"):
                warnings.append(f"plans[{idx}].steps[{step_idx}].url does not look like a Players Club event detail URL")

    notes = data.get("notes", [])
    if notes is not None and not isinstance(notes, list):
        errors.append("notes must be a list when present")

    return errors, warnings, total_events, len(plans)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate pokeca event JSON for site generation")
    parser.add_argument("events_json")
    parser.add_argument("--require-future-target", action="store_true", help="Fail when target_date is before today")
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.events_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors, warnings, total_events, plan_count = validate(data, args.require_future_target)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {total_events} events, {plan_count} plans")


if __name__ == "__main__":
    main()
