#!/usr/bin/env python3
"""
ポケカ イベントレポート HTML生成スクリプト

JSONデータからGitHub Pages用のHTMLページを生成する。

使用方法:
  python3 generate_page.py /path/to/pokeca_event_MMDD.json [--output /path/to/index.html]

入力JSON形式:
  {
    "meta": {
      "report_date": "2026/03/20",
      "report_day": "金",
      "target_date": "2026/03/22",
      "target_day": "日",
      "area": "大阪府",
      "search_url": "https://players.pokemon-card.com/event/search",
      "total_events": 106
    },
    "events": {
      "gym_battle": [...],
      "open_league": [...],
      "friend_battle": [...],
      "self_event": [...]
    },
    "plans": [...],
    "notes": [...]
  }
"""

import argparse
import json
import os
import re

CATEGORY_CONFIG = {
    "gym_battle": {
        "name": "ジムバトル",
        "color": "#2563eb",
        "icon": "&#9876;"
    },
    "open_league": {
        "name": "オープンリーグ / トレーナーズリーグ",
        "color": "#d97706",
        "icon": "&#127942;"
    },
    "friend_battle": {
        "name": "いっしょにフレンドバトル",
        "color": "#059669",
        "icon": "&#129309;"
    },
    "self_event": {
        "name": "参考：自主イベント・杯戦",
        "color": "#7c3aed",
        "icon": "&#127919;"
    }
}

AREA_IDS = {
    "大阪府": "osaka",
    "京都府": "kyoto",
    "兵庫県": "hyogo",
    "奈良県": "nara",
    "滋賀県": "shiga",
    "和歌山県": "wakayama",
}

LOCATION_FILTERS = [
    {
        "id": "all",
        "name": "全エリア",
        "description": "掲載候補をすべて表示",
        "keywords": [],
    },
    {
        "id": "namba-umeda",
        "name": "なんば・梅田周辺",
        "description": "なんば、日本橋、梅田、大阪駅、茶屋町周辺だけを表示",
        "keywords": [
            "なんば",
            "難波",
            "日本橋",
            "浪速区",
            "梅田",
            "大阪駅",
            "大阪駅前",
            "茶屋町",
            "芝田",
        ],
    },
]


def build_categories(events_dict):
    """フィルタ済みイベント辞書からカテゴリ配列を構築"""
    categories = []
    for cat_id in ["gym_battle", "open_league", "friend_battle", "self_event"]:
        evts = events_dict.get(cat_id, [])
        if not evts:
            continue
        cfg = CATEGORY_CONFIG[cat_id]
        cat_events = []
        for i, ev in enumerate(evts):
            tags = detect_tags(ev, cat_id)
            cat_events.append({
                "id": ev.get("id", i + 1),
                "time": ev.get("datetime", ""),
                "name": ev.get("name", ""),
                "venue": ev.get("venue", ""),
                "address": ev.get("address", ""),
                "fee": ev.get("fee", ""),
                "capacity": ev.get("capacity", ""),
                "distance": f"約{ev.get('travel_time', '?')}分",
                "url": ev.get("url", ""),
                "tags": tags
            })
        categories.append({
            "id": cat_id,
            "name": cfg["name"],
            "color": cfg["color"],
            "events": cat_events
        })
    return categories


def detect_tags(event, category):
    """イベント情報からタグを自動検出"""
    tags = []
    name = event.get("name", "")
    cap_str = str(event.get("capacity", ""))
    datetime_str = event.get("datetime", "")
    travel = event.get("travel_time", 99)

    # CSP対象
    if any(k in name for k in ["オープンリーグ", "トレーナーズリーグ", "シティリーグ"]):
        tags.append("csp")

    # 満席
    if event.get("is_full"):
        tags.append("full")

    # 大型大会
    cap_match = re.search(r"(\d+)", cap_str)
    if cap_match and int(cap_match.group(1)) >= 64:
        tags.append("large")

    # 駅近
    if isinstance(travel, (int, float)) and travel <= 5:
        tags.append("near")

    # 長時間開催
    if "〜" in datetime_str:
        parts = datetime_str.split("〜")
        if len(parts) == 2 and parts[0] and parts[1]:
            try:
                start_h = int(parts[0].split(":")[0])
                end_h = int(parts[1].split(":")[0])
                if end_h - start_h >= 6:
                    tags.append("long")
                if end_h >= 21:
                    tags.append("night")
            except (ValueError, IndexError):
                pass

    # 初心者歓迎
    if category == "friend_battle":
        tags.append("beginner")

    return tags


def build_context_notes(raw_data):
    """構造化された確認結果をサイトの注意事項へ追加する。"""
    notes = []

    favorite_filters = raw_data.get("favorite_shop_filters", [])
    if isinstance(favorite_filters, list) and favorite_filters:
        for item in favorite_filters:
            if not isinstance(item, dict):
                continue
            venue = item.get("venue", "")
            capacity = item.get("capacity_summary") or item.get("capacity", "")
            conditions = item.get("filter_conditions", "")
            if venue and conditions:
                detail = f"{venue}"
                if capacity:
                    detail += f"（{capacity}）"
                detail += f": {conditions}"
                notes.append("お気に入り店舗フィルター: " + detail)

    venue_checks = raw_data.get("venue_checks", {})
    girafull_check = venue_checks.get("girafull_namba_x") if isinstance(venue_checks, dict) else None
    if isinstance(girafull_check, dict):
        floor = girafull_check.get("floor", "")
        label_color = girafull_check.get("label_color", "")
        summary = girafull_check.get("summary", "")
        post_url = girafull_check.get("schedule_post_url", "")
        image_url = girafull_check.get("image_url", "")
        pieces = []
        if floor:
            pieces.append(f"フロア: {floor}")
        if label_color:
            pieces.append(f"ラベル色: {label_color}")
        if summary:
            pieces.append(summary)
        if post_url:
            pieces.append(f"確認ポスト: {post_url}")
        if image_url:
            pieces.append(f"原寸画像: {image_url}")
        if pieces:
            notes.append("GIRAFULLなんば Xスケジュール確認: " + " / ".join(pieces))
        target_day_events = girafull_check.get("target_day_events", [])
        if isinstance(target_day_events, list):
            event_summaries = []
            for event in target_day_events:
                if not isinstance(event, dict):
                    continue
                time = event.get("time", "")
                type_code = event.get("type_code", "")
                name = event.get("event", "")
                event_floor = event.get("floor", "")
                event_color = event.get("label_color", "")
                capacity = event.get("capacity", "")
                fee = event.get("fee", "")
                detail = " ".join(part for part in (time, type_code, name) if part)
                meta_parts = []
                if event_floor:
                    meta_parts.append(f"階: {event_floor}")
                if event_color:
                    meta_parts.append(f"ラベル色: {event_color}")
                if capacity:
                    meta_parts.append(f"定員: {capacity}")
                if fee:
                    meta_parts.append(f"参加費: {fee}")
                meta = " / ".join(meta_parts)
                if detail and meta:
                    event_summaries.append(f"{detail}（{meta}）")
            if event_summaries:
                notes.append("GIRAFULLなんば X対象日イベント: " + "、".join(event_summaries))

    return notes


def generate_html(data):
    """データからHTML文字列を生成"""
    # index.htmlのテンプレートを読み込み、DATAを置換
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "..", "index.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # DATA部分を置換
    data_json = json.dumps(data, ensure_ascii=False, indent=2)

    # const DATA = { ... }; の部分を置換
    pattern = r"const DATA = \{[\s\S]*?\n\};"
    replacement = f"const DATA = {data_json};"
    new_html, replace_count = re.subn(pattern, lambda _match: replacement, template)
    if replace_count != 1:
        raise ValueError("index.html template must contain exactly one `const DATA = ...;` block")

    # titleも更新
    first_date = data.get("dates", [{}])[0]
    first_area_id = next(iter(first_date.get("areaData", {}) or {}), "")
    area_name = next(
        (area.get("name", "") for area in data.get("areas", []) if area.get("id") == first_area_id),
        "",
    )
    new_title = f"ポケカ イベント {first_date.get('date', '')}（{first_date.get('day', '')}）{area_name}"
    new_html = re.sub(r"<title>.*?</title>", f"<title>{new_title}</title>", new_html)

    return new_html


def area_id_for(area):
    if area in AREA_IDS:
        return AREA_IDS[area]
    normalized = re.sub(r"[^0-9A-Za-z]+", "-", area).strip("-").lower()
    return normalized or "area"


def parse_args():
    parser = argparse.ArgumentParser(description="ポケカイベントJSONからGitHub Pages用HTMLを生成する")
    parser.add_argument("events_json", help="イベント収集・行動プラン生成済みJSON")
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"),
        help="生成先HTML。既定値: リポジトリ直下のindex.html",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    json_path = args.events_json

    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # フィルタ済みイベントデータからページデータを構築
    meta = raw_data.get("meta", {})
    events = raw_data.get("events", {})
    categories = build_categories(events)

    filtered_count = sum(len(c["events"]) for c in categories)

    area = meta.get("area", "大阪府")
    target_date = meta.get("target_date", "")
    target_day = meta.get("target_day", "日")
    area_id = area_id_for(area)
    notes = list(raw_data.get("notes", []) or [])
    notes.extend(build_context_notes(raw_data))
    area_data = {
        "totalEvents": meta.get("total_events", 0),
        "filteredCount": filtered_count,
        "criteria": meta.get("criteria", ""),
        "categories": categories,
        "plans": raw_data.get("plans", []),
        "locationFilters": raw_data.get("location_filters", LOCATION_FILTERS),
        "focusPlans": raw_data.get("focus_plans", {}),
        "notes": notes,
    }

    page_data = {
        "meta": {
            "region": meta.get("region", area),
            "searchUrl": meta.get("search_url", "https://players.pokemon-card.com/event/search"),
            "reportDate": f"{meta.get('report_date', '')}（{meta.get('report_day', '')}）",
        },
        "areas": [{"id": area_id, "name": area}],
        "dates": [
            {
                "date": target_date,
                "day": target_day,
                "areaData": {
                    area_id: area_data,
                },
            }
        ],
    }

    html = generate_html(page_data)

    # 出力
    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print(f"Events: {filtered_count} ({len(categories)} categories)")


if __name__ == "__main__":
    main()
