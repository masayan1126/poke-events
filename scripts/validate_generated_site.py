#!/usr/bin/env python3
"""Validate generated HTML so automation fails before a broken deploy."""

import argparse
import html as html_lib
import json
import re
import sys


def extract_site_data_script(html):
    match = re.search(r'<script[^>]*id="site-data"[^>]*>([\s\S]*?)</script>', html)
    if not match:
        return None
    return html_lib.unescape(match.group(1))


def extract_data_block(html):
    script_data = extract_site_data_script(html)
    if script_data:
        return script_data

    match = re.search(r"const DATA = ([\s\S]*?\n})(?=;)", html)
    if not match:
        return None
    return match.group(1)


def try_parse_json_data(data_block):
    try:
        return json.loads(data_block)
    except json.JSONDecodeError:
        return None


def normalize_text(value):
    return re.sub(r"\s+", "", str(value or "").replace("　", " "))


def contains_girafull(value):
    return "GIRAFULLなんば" in normalize_text(value) or "ジラフルなんば" in normalize_text(value)


def collect_values(value):
    values = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(collect_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(collect_values(item))
    elif value is not None:
        values.append(str(value))
    return values


def validate_girafull_notes(area_id, data, errors):
    candidate_values = []
    for key in ("categories", "plans", "focusPlans"):
        candidate_values.extend(collect_values(data.get(key)))
    if not any(contains_girafull(value) for value in candidate_values):
        return

    notes = data.get("notes", [])
    if not isinstance(notes, list):
        errors.append(f"DATA area {area_id} notes must be a list when GIRAFULL is present")
        return

    notes_text = "\n".join(str(note) for note in notes)
    normalized_notes = normalize_text(notes_text)
    required_patterns = {
        "GIRAFULL X schedule note": "GIRAFULLなんばXスケジュール確認",
        "GIRAFULL target-day event note": "GIRAFULLなんばX対象日イベント",
        "GIRAFULL X status URL": "https://x.com/GIRAFULL_Namba/status/",
        "GIRAFULL original image URL": "https://pbs.twimg.com/media/",
        "GIRAFULL label color": "ラベル色",
        "GIRAFULL event floor": "F",
        "GIRAFULL event capacity": "人",
        "GIRAFULL event fee": "参加費",
    }
    for label, pattern in required_patterns.items():
        if normalize_text(pattern) not in normalized_notes:
            errors.append(f"DATA area {area_id} notes must include {label}")


def validate_html(html):
    errors = []

    has_next_data = extract_site_data_script(html) is not None
    has_legacy_data = html.count("const DATA = ") == 1
    if not has_next_data and not has_legacy_data:
        errors.append("HTML must contain a site-data JSON script or exactly one const DATA block")
        return errors

    data_block = extract_data_block(html)
    if data_block is None:
        errors.append("const DATA block could not be extracted")
        return errors

    if 'class="plans-section"' not in html:
        errors.append("plans section is missing")
    if 'class="events-area"' not in html and 'id="eventsContainer"' not in html:
        errors.append("events area is missing")
    if not re.search(r'"plans"\s*:\s*\[|plans\s*:', data_block):
        errors.append("plans data is missing from DATA")
    if re.search(r'("plans"|plans)\s*:\s*\[\s*\]', data_block):
        errors.append("DATA contains an empty plans array")
    if not re.search(r'"categories"\s*:\s*\[|categories\s*:', data_block):
        errors.append("categories data is missing from DATA")
    if not re.search(r'"dates"\s*:\s*\[|dates\s*:', data_block):
        errors.append("dates data is missing from DATA")
    if not re.search(r'"areas"\s*:\s*\[|areas\s*:', data_block):
        errors.append("areas data is missing from DATA")
    if not re.search(r"<title>ポケカ イベント|<title>ポケカ イベントプラン", html):
        errors.append("generated title was not updated")

    parsed = try_parse_json_data(data_block)
    if parsed is None:
        errors.append("DATA block is not valid JSON")
    else:
        dates = parsed.get("dates", [])
        areas = parsed.get("areas", [])
        if not dates:
            errors.append("DATA.dates must contain at least one date")
        if not areas:
            errors.append("DATA.areas must contain at least one area")
        for date_idx, date_entry in enumerate(dates, start=1):
            area_data = date_entry.get("areaData", {})
            if not area_data:
                errors.append(f"DATA.dates[{date_idx}].areaData must not be empty")
                continue
            for area_id, data in area_data.items():
                plans = data.get("plans", [])
                categories = data.get("categories", [])
                if not 3 <= len(plans) <= 4:
                    errors.append(f"DATA area {area_id} must contain 3 or 4 plans")
                if not categories:
                    errors.append(f"DATA area {area_id} must contain categories")
                validate_girafull_notes(area_id, data, errors)
                location_filters = data.get("locationFilters", [])
                if location_filters:
                    filter_ids = {item.get("id") for item in location_filters if isinstance(item, dict)}
                    if "all" not in filter_ids:
                        errors.append(f"DATA area {area_id} locationFilters must include all")
                    if "namba-umeda" in filter_ids:
                        focus_plans = data.get("focusPlans", {})
                        namba_umeda_plans = focus_plans.get("namba-umeda") if isinstance(focus_plans, dict) else None
                        if not isinstance(namba_umeda_plans, list) or not namba_umeda_plans:
                            errors.append(f"DATA area {area_id} must contain namba-umeda focusPlans")

    return errors


def parse_args():
    parser = argparse.ArgumentParser(description="Validate generated pokeca event HTML")
    parser.add_argument("html_path")
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.html_path, "r", encoding="utf-8") as f:
        html = f.read()

    errors = validate_html(html)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {args.html_path}")


if __name__ == "__main__":
    main()
