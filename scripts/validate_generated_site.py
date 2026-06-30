#!/usr/bin/env python3
"""Validate generated HTML so automation fails before a broken deploy."""

import argparse
import json
import re
import sys


def extract_data_block(html):
    match = re.search(r"const DATA = ([\s\S]*?\n})(?=;)", html)
    if not match:
        return None
    return match.group(1)


def try_parse_json_data(data_block):
    try:
        return json.loads(data_block)
    except json.JSONDecodeError:
        return None


def validate_html(html):
    errors = []

    if html.count("const DATA = ") != 1:
        errors.append("HTML must contain exactly one const DATA block")
        return errors

    data_block = extract_data_block(html)
    if data_block is None:
        errors.append("const DATA block could not be extracted")
        return errors

    if '<section class="plans-section"' not in html:
        errors.append("plans section is missing")
    if 'id="eventsContainer"' not in html:
        errors.append("events container is missing")
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
    if not re.search(r"<title>ポケカ イベント .+</title>", html) or "（）</title>" in html:
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
