#!/usr/bin/env python3
"""Validate the event JSON contract before generating the static site."""

import argparse
import json
import re
import sys
from datetime import date, datetime


EVENT_CATEGORIES = ("gym_battle", "open_league", "friend_battle", "self_event")
REQUIRED_META = ("report_date", "target_date", "area")
REQUIRED_EVENT_FIELDS = ("datetime", "name", "venue", "address")
REQUIRED_PLAN_FIELDS = ("id", "name", "subtitle", "rating", "steps", "merit")
REQUIRED_STEP_FIELDS = ("time", "event", "venue", "area")
FAVORITE_SHOPS = (
    "おじゃま館蒲生店",
    "あっぷる 今福店",
    "カードショップきりん 大阪天満橋店",
    "トレカWIN",
)
GIRAFULL_NAMBA_PATTERNS = ("GIRAFULLなんば", "ジラフルなんば")
GIRAFULL_NAMBA_X_URL = "https://x.com/GIRAFULL_Namba"
REQUIRED_GIRAFULL_X_FIELDS = (
    "account_url",
    "schedule_post_url",
    "image_url",
    "schedule_month",
    "target_date",
    "floor",
    "label_color",
    "target_day_events",
    "summary",
)
REQUIRED_GIRAFULL_TARGET_EVENT_FIELDS = (
    "time",
    "type_code",
    "event",
    "floor",
    "label_color",
    "capacity",
    "fee",
)


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


def _parse_schedule_month(value):
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    match = re.fullmatch(r"(\d{4})[-/](\d{1,2})", normalized)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.fullmatch(r"(\d{4})年\s*(\d{1,2})月", normalized)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def _is_girafull_x_post_url(value):
    if not isinstance(value, str):
        return False
    return value.startswith("https://x.com/GIRAFULL_Namba/status/")


def _is_girafull_media_url(value):
    if not isinstance(value, str):
        return False
    return value.startswith("https://pbs.twimg.com/media/")


def _normalize_text(value):
    return re.sub(r"\s+", "", str(value or "").replace("　", " "))


def _matches_any(value, patterns):
    normalized = _normalize_text(value)
    return any(_normalize_text(pattern) in normalized for pattern in patterns)


def _flatten_events(events):
    flattened = []
    for category in EVENT_CATEGORIES:
        category_events = events.get(category, [])
        if isinstance(category_events, list):
            flattened.extend(event for event in category_events if isinstance(event, dict))
    return flattened


def _plan_uses_venue(plans, patterns):
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        for step in plan.get("steps", []):
            if isinstance(step, dict) and _matches_any(step.get("venue", ""), patterns):
                return True
    return False


def _validate_favorite_shop_filters(data, events, errors):
    meta = data.get("meta")
    area = str(meta.get("area", "")) if isinstance(meta, dict) else ""
    flattened_events = _flatten_events(events)
    should_require = "大阪" in area or any(
        _matches_any(event.get("venue", ""), FAVORITE_SHOPS) for event in flattened_events
    )
    if not should_require:
        return

    filters = data.get("favorite_shop_filters")
    if not isinstance(filters, list):
        errors.append("favorite_shop_filters must be a list for Osaka event generation")
        return

    entries_by_venue = {}
    for idx, entry in enumerate(filters, start=1):
        if not isinstance(entry, dict):
            errors.append(f"favorite_shop_filters[{idx}] must be an object")
            continue
        venue = entry.get("venue")
        if not _is_non_empty_string(venue):
            errors.append(f"favorite_shop_filters[{idx}].venue is required")
            continue
        entries_by_venue[_normalize_text(venue)] = entry
        if not _is_non_empty_string(entry.get("filter_conditions")):
            errors.append(f"favorite_shop_filters[{idx}].filter_conditions is required")
        if not (
            _is_non_empty_string(entry.get("capacity"))
            or _is_non_empty_string(entry.get("capacity_summary"))
            or _is_non_empty_string(entry.get("participant_count"))
        ):
            errors.append(f"favorite_shop_filters[{idx}] must include capacity, capacity_summary, or participant_count")

    for shop in FAVORITE_SHOPS:
        entry = entries_by_venue.get(_normalize_text(shop))
        if entry is None:
            errors.append(f"favorite_shop_filters must include {shop}")


def _validate_girafull_namba_x_check(data, events, plans, target_date, errors, warnings):
    flattened_events = _flatten_events(events)
    has_girafull_event = any(
        _matches_any(event.get("venue", ""), GIRAFULL_NAMBA_PATTERNS) for event in flattened_events
    )
    has_girafull_plan = _plan_uses_venue(plans, GIRAFULL_NAMBA_PATTERNS)
    if not has_girafull_event and not has_girafull_plan:
        return

    venue_checks = data.get("venue_checks")
    if not isinstance(venue_checks, dict):
        errors.append("venue_checks.girafull_namba_x is required when events or plans include GIRAFULLなんば")
        return

    check = venue_checks.get("girafull_namba_x")
    if not isinstance(check, dict):
        errors.append("venue_checks.girafull_namba_x must be an object when events or plans include GIRAFULLなんば")
        return

    for field in REQUIRED_GIRAFULL_X_FIELDS:
        if field == "target_day_events":
            continue
        if not _is_non_empty_string(check.get(field)):
            errors.append(f"venue_checks.girafull_namba_x.{field} is required")
    if check.get("account_url") != GIRAFULL_NAMBA_X_URL:
        errors.append(f"venue_checks.girafull_namba_x.account_url must be {GIRAFULL_NAMBA_X_URL}")
    if check.get("schedule_post_url") and not _is_girafull_x_post_url(check.get("schedule_post_url")):
        errors.append("venue_checks.girafull_namba_x.schedule_post_url must be a GIRAFULL_Namba X status URL")
    if check.get("image_url") and not _is_girafull_media_url(check.get("image_url")):
        errors.append("venue_checks.girafull_namba_x.image_url must be a pbs.twimg.com media URL")

    check_target_date = _parse_yyyy_mm_dd(check.get("target_date"))
    if check.get("target_date") and check_target_date is None:
        errors.append("venue_checks.girafull_namba_x.target_date must be YYYY/MM/DD or YYYY-MM-DD")
    elif target_date and check_target_date and check_target_date != target_date:
        errors.append("venue_checks.girafull_namba_x.target_date must match meta.target_date")

    schedule_month = _parse_schedule_month(check.get("schedule_month"))
    if check.get("schedule_month") and schedule_month is None:
        errors.append("venue_checks.girafull_namba_x.schedule_month must be YYYY-MM, YYYY/MM, or YYYY年M月")
    elif target_date and schedule_month and schedule_month != (target_date.year, target_date.month):
        errors.append("venue_checks.girafull_namba_x.schedule_month must match meta.target_date month")

    target_day_events = check.get("target_day_events")
    if not isinstance(target_day_events, list) or not target_day_events:
        errors.append("venue_checks.girafull_namba_x.target_day_events must be a non-empty list")
        return
    for idx, event in enumerate(target_day_events, start=1):
        if not isinstance(event, dict):
            errors.append(f"venue_checks.girafull_namba_x.target_day_events[{idx}] must be an object")
            continue
        for field in REQUIRED_GIRAFULL_TARGET_EVENT_FIELDS:
            if not _is_non_empty_string(event.get(field)):
                errors.append(f"venue_checks.girafull_namba_x.target_day_events[{idx}].{field} is required")


def _validate_plan_object(plan, label, errors, warnings):
    if not isinstance(plan, dict):
        errors.append(f"{label} must be an object")
        return

    for field in REQUIRED_PLAN_FIELDS:
        if field not in plan:
            errors.append(f"{label}.{field} is required")

    plan_id = plan.get("id")
    if plan_id is None or not str(plan_id).strip():
        errors.append(f"{label}.id is required")

    rating = plan.get("rating")
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        errors.append(f"{label}.rating must be an integer from 1 to 5")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(f"{label}.steps must be a non-empty list")
        return

    for step_idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"{label}.steps[{step_idx}] must be an object")
            continue
        for field in REQUIRED_STEP_FIELDS:
            if not _is_non_empty_string(step.get(field)):
                errors.append(f"{label}.steps[{step_idx}].{field} is required")
        if "url" in step and step["url"] and not str(step["url"]).startswith("https://players.pokemon-card.com/event/detail/"):
            warnings.append(f"{label}.steps[{step_idx}].url does not look like a Players Club event detail URL")


def _validate_focus_plans(data, errors, warnings):
    focus_plans = data.get("focus_plans")
    if focus_plans is None:
        return
    if not isinstance(focus_plans, dict):
        errors.append("focus_plans must be an object when present")
        return
    for focus_id, plans in focus_plans.items():
        if not isinstance(focus_id, str) or not focus_id.strip():
            errors.append("focus_plans keys must be non-empty strings")
        if not isinstance(plans, list) or not plans:
            errors.append(f"focus_plans.{focus_id} must be a non-empty list")
            continue
        for idx, plan in enumerate(plans, start=1):
            _validate_plan_object(plan, f"focus_plans.{focus_id}[{idx}]", errors, warnings)


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
        _validate_plan_object(plan, f"plans[{idx}]", errors, warnings)
        if not isinstance(plan, dict):
            continue

        plan_id = plan.get("id")
        if plan_id and plan_id in seen_plan_ids:
            errors.append(f"plans[{idx}].id duplicates another plan")
        elif plan_id:
            seen_plan_ids.add(plan_id)

    notes = data.get("notes", [])
    if notes is not None and not isinstance(notes, list):
        errors.append("notes must be a list when present")

    _validate_focus_plans(data, errors, warnings)
    _validate_favorite_shop_filters(data, events, errors)
    _validate_girafull_namba_x_check(data, events, plans, target_date, errors, warnings)

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
