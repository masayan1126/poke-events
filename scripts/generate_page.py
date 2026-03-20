#!/usr/bin/env python3
"""
ポケカ イベントレポート HTML生成スクリプト

JSONデータからGitHub Pages用のHTMLページを生成する。

使用方法:
  python3 generate_page.py /path/to/pokeca_event_MMDD.json [--plans /path/to/plans.json]

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

import json
import sys
import os

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
    import re
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
    import re
    pattern = r"const DATA = \{[\s\S]*?\n\};"
    replacement = f"const DATA = {data_json};"
    new_html = re.sub(pattern, replacement, template)

    # titleも更新
    meta = data.get("meta", {})
    new_title = f"ポケカ イベント {meta.get('targetDate', '')}（{meta.get('targetDay', '')}）{meta.get('area', '')}"
    new_html = re.sub(r"<title>.*?</title>", f"<title>{new_title}</title>", new_html)

    return new_html


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 generate_page.py <events.json>", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]

    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # フィルタ済みイベントデータからページデータを構築
    meta = raw_data.get("meta", {})
    events = raw_data.get("events", {})
    categories = build_categories(events)

    filtered_count = sum(len(c["events"]) for c in categories)

    page_data = {
        "meta": {
            "reportDate": f"{meta.get('report_date', '')}（{meta.get('report_day', '')}）",
            "targetDate": meta.get("target_date", ""),
            "targetDay": meta.get("target_day", "日"),
            "area": meta.get("area", "大阪府"),
            "searchUrl": meta.get("search_url", "https://players.pokemon-card.com/event/search"),
            "totalEvents": meta.get("total_events", 0),
            "filteredCount": filtered_count,
            "criteria": meta.get("criteria", "")
        },
        "categories": categories,
        "plans": raw_data.get("plans", []),
        "notes": raw_data.get("notes", [])
    }

    html = generate_html(page_data)

    # 出力
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print(f"Events: {filtered_count} ({len(categories)} categories)")


if __name__ == "__main__":
    main()
